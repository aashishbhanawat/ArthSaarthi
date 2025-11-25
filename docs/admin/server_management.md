# Server Administration Guide: Backup, Restore, and Upgrades

This guide is intended for system administrators who are self-hosting the ArthSaarthi application in a server environment using Docker. It covers the standard procedures for performing application upgrades and handling database backups and restores.

**Important:** The procedures described here are for administrative, database-level operations. This is different from the user-facing JSON backup feature, which is designed for individual users to export their own data.

## The Strategy: Database Backup & Alembic Migrations

For server-wide upgrades and disaster recovery, we rely on two core components:

1.  **`pg_dump`:** A standard PostgreSQL utility to create a complete, portable, and reliable backup of the entire application database.
2.  **Alembic:** The application's built-in database migration tool. For most version upgrades, Alembic will handle any database schema changes automatically. The database backup serves as a critical safety net.

---

## Standard Upgrade Procedure

Follow these steps to upgrade your self-hosted ArthSaarthi instance to a new version.

### Step 1: (Optional but Recommended) Maintenance Mode

Stop the application containers to prevent users from making changes to the database while you perform the backup.

```bash
docker-compose stop backend frontend
```

### Step 2: Create a Full Database Backup

This is the most critical step. From the root directory of the project (where your `docker-compose.yml` file is), run the following command to create a timestamped backup file on your host machine.

```bash
docker-compose exec -T db pg_dump -U postgres -d arthsaarthi_db -Fc > arthsaarthi_backup_$(date +%Y-%m-%d).dump
```

**Command Breakdown:**
*   `docker-compose exec -T db`: Executes a command inside the running `db` (PostgreSQL) container.
*   `pg_dump`: The PostgreSQL backup utility.
*   `-U postgres`: Connects as the `postgres` user (or your configured user).
*   `-d arthsaarthi_db`: Specifies the database to back up.
*   `-Fc`: Creates the backup in a custom, compressed, and flexible format.
*   `> ... .dump`: Redirects the output to a file on your host machine.

### Step 3: Upgrade the Application Code

Update the application source code to the new version and rebuild the Docker images.

```bash
# Stop all services
docker-compose down

# Get the latest code
git pull origin main  # Or checkout a specific release tag

# Rebuild the Docker images with the new code
docker-compose build
```

### Step 4: Run Database Migrations

Start the database and allow the application's entrypoint script to automatically apply any necessary schema migrations using Alembic.

```bash
docker-compose up -d db
docker-compose run --rm backend alembic upgrade head
```

The `alembic upgrade head` command applies any new migration scripts from the updated codebase to your existing database, bringing its schema up to date without losing data.

### Step 5: Start the New Application Version

You can now start the full application.

```bash
docker-compose up -d
```

The upgrade is now complete.

---

## Disaster Recovery: Restoring from a Backup

You would only need to restore the `.dump` file in a disaster recovery scenario (e.g., a failed upgrade, data corruption, or migration to a new server).

1.  **Ensure a clean state.** Stop and remove the old containers and database volume: `docker-compose down -v`.
2.  **Start the database service:** `docker-compose up -d db`.
3.  **Copy the backup file into the container:**
    ```bash
    docker-compose cp arthsaarthi_backup_YYYY-MM-DD.dump db:/tmp/backup.dump
    ```
4.  **Execute the restore command:**
    ```bash
    docker-compose exec -T db pg_restore -U postgres -d arthsaarthi_db --clean --if-exists /tmp/backup.dump
    ```
5.  **Proceed with the standard upgrade process** from Step 4 (Run Database Migrations) onwards to ensure the restored database schema is up-to-date with the application code.