# PyInstaller hook for pdfplumber
# This ensures pdfplumber and all its dependencies are properly bundled

from PyInstaller.utils.hooks import collect_all, collect_submodules

# Collect pdfplumber and all submodules
hiddenimports = collect_submodules('pdfplumber')
hiddenimports += collect_submodules('pdfminer')
hiddenimports += collect_submodules('pdfminer.six')

# Collect all data files and binaries needed by pdfplumber
datas, binaries, hiddenimports_extra = collect_all('pdfplumber')
hiddenimports += hiddenimports_extra
