import sys

with open("backend/app/crud/crud_holding.py", "r") as f:
    content = f.read()

# We need to extract the inner logic of get_portfolio_holdings_and_summary into a private method
# _calculate_holdings_and_summary_from_data

new_methods = """
    def _calculate_holdings_and_summary_from_data(
        self,
        db: Session,
        portfolio_id: uuid.UUID,
        transactions: List[models.Transaction],
        all_fixed_deposits: List[models.FixedDeposit],
        all_recurring_deposits: List[models.RecurringDeposit],
        all_portfolio_assets: List[models.Asset]
    ) -> schemas.PortfolioHoldingsAndSummary:
        start_time = time.time()
        logger.info(
            f"Starting holdings calculation for portfolio_id: {portfolio_id} from data"
        )

        # --- Process Market-Traded Assets First ---
        market_traded_holdings, total_realized_pnl = _process_market_traded_assets(
            db, portfolio_id, transactions, Decimal("0.0")
        )
        logger.info(
            f"Processed {len(market_traded_holdings)} market-traded assets. "
            f"Realized PNL from sales: {total_realized_pnl}"
        )
        holdings_list: List[schemas.Holding] = market_traded_holdings

        # --- Process Non-Market-Traded Assets (FDs, RDs, PPF) ---
        fd_holdings, pnl_from_matured_fds = _process_fixed_deposits(all_fixed_deposits)
        rd_holdings, pnl_from_matured_rds = _process_recurring_deposits(
            all_recurring_deposits
        )
        logger.info(
            "Processed FDs (%s), RDs (%s).", len(fd_holdings), len(rd_holdings)
        )
        logger.info(
            "Realized PNL from matured FDs: %s, RDs: %s",
            pnl_from_matured_fds,
            pnl_from_matured_rds,
        )
        holdings_list.extend(fd_holdings)
        holdings_list.extend(rd_holdings)
        total_realized_pnl += pnl_from_matured_fds + pnl_from_matured_rds

        ppf_assets = [
            asset for asset in all_portfolio_assets if asset.asset_type.upper() == "PPF"
        ]
        logger.info(f"Found {len(ppf_assets)} PPF assets to process.")
        # --- PPF Holdings ---
        for ppf_asset in ppf_assets:
            db.query(models.Asset).filter_by(id=ppf_asset.id).with_for_update().first()
            logger.info(f"Processing PPF asset {ppf_asset.id}...")
            ppf_holding = process_ppf_holding(db, ppf_asset, portfolio_id)
            if ppf_holding:
                holdings_list.append(ppf_holding)
                if ppf_holding.realized_pnl:
                    logger.debug(
                        "  - PPF Holding Realized PNL: %s", ppf_holding.realized_pnl
                    )

        logger.info("Finished processing all PPF assets.")

        # --- Final Grouping and Summary Calculation ---
        logger.info(
            f"Starting final summary. Total holdings in list: {len(holdings_list)}"
        )
        for holding_item in holdings_list:
            group_map = {
                "STOCK": "EQUITIES",
                "Mutual Fund": "EQUITIES",
                "MUTUAL_FUND": "EQUITIES",
                "ETF": "EQUITIES",
                "FIXED_DEPOSIT": "DEPOSITS",
                "RECURRING_DEPOSIT": "DEPOSITS",
                "BOND": "BONDS",
                "PPF": "GOVERNMENT_SCHEMES",
            }
            group_map_upper = {k.upper(): v for k, v in group_map.items()}
            holding_item.group = group_map_upper.get(
                str(holding_item.asset_type).upper(), "MISCELLANEOUS")

        # --- Calculate Unrealized P&L for all holdings ---
        for holding in holdings_list:
            if holding.asset_type not in ["FIXED_DEPOSIT", "RECURRING_DEPOSIT", "PPF"]:
                unrealized_pnl = holding.current_value - holding.total_invested_amount
            else:
                unrealized_pnl = holding.unrealized_pnl

            holding.unrealized_pnl = unrealized_pnl
            if holding.total_invested_amount > 0:
                holding.unrealized_pnl_percentage = float(
                    unrealized_pnl / holding.total_invested_amount
                )

        summary = _calculate_summary(holdings_list, total_realized_pnl, transactions)
        logger.info(
            f"Calculation complete. Total portfolio value: {summary.total_value}"
        )
        logger.debug(
            "[_calculate_holdings_and_summary_from_data] Final summary object: %s", summary
        )
        end_time = time.time()
        logger.info(
            f"Holdings calculation for portfolio {portfolio_id} "
            f"took {end_time - start_time:.4f} seconds."
        )

        return schemas.PortfolioHoldingsAndSummary(
            summary=summary, holdings=holdings_list
        )

    def get_multiple_portfolios_holdings_and_summary(
        self, db: Session, *, portfolio_ids: List[uuid.UUID]
    ) -> Dict[uuid.UUID, schemas.PortfolioHoldingsAndSummary]:
        if not portfolio_ids:
            return {}

        all_transactions = crud.transaction.get_multi_by_portfolios(
            db=db, portfolio_ids=portfolio_ids
        )
        all_fixed_deposits = crud.fixed_deposit.get_multi_by_portfolios(
            db=db, portfolio_ids=portfolio_ids
        )
        all_recurring_deposits = crud.recurring_deposit.get_multi_by_portfolios(
            db=db, portfolio_ids=portfolio_ids
        )
        all_portfolio_assets = crud.asset.get_multi_by_portfolios(
            db=db, portfolio_ids=portfolio_ids
        )

        from collections import defaultdict

        txs_by_port = defaultdict(list)
        for tx in all_transactions:
            txs_by_port[tx.portfolio_id].append(tx)

        fds_by_port = defaultdict(list)
        for fd in all_fixed_deposits:
            fds_by_port[fd.portfolio_id].append(fd)

        rds_by_port = defaultdict(list)
        for rd in all_recurring_deposits:
            rds_by_port[rd.portfolio_id].append(rd)

        # Assets can be associated via transactions, but get_multi_by_portfolios
        # returns all assets that have transactions in any of the portfolios.
        # PPF assets logic in process_ppf_holding uses asset.id.
        # Actually crud.asset.get_multi_by_portfolio returns assets based on transactions
        # for a specific portfolio. So get_multi_by_portfolios returns all of them.
        # We can just pass all_portfolio_assets to each, since process_ppf_holding filters
        # by portfolio_id anyway when querying transactions internally. But wait, we should
        # filter them to just the ones related to the portfolio.
        # A simpler approach: process_ppf_holding already fetches transactions internally for the portfolio
        # But wait, it might query again. It's OK, PPF is rare.

        results = {}
        for p_id in portfolio_ids:
            # We filter assets by checking if there's any transaction for this asset in this portfolio
            p_asset_ids = {tx.asset_id for tx in txs_by_port[p_id]}
            p_assets = [a for a in all_portfolio_assets if a.id in p_asset_ids]

            results[p_id] = self._calculate_holdings_and_summary_from_data(
                db=db,
                portfolio_id=p_id,
                transactions=txs_by_port[p_id],
                all_fixed_deposits=fds_by_port[p_id],
                all_recurring_deposits=rds_by_port[p_id],
                all_portfolio_assets=p_assets
            )

        return results
"""
