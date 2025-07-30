import typer
from .checker import check_column_types

app = typer.Typer()

@app.command()
def main(db_url: str):
    mismatches = check_column_types(db_url)
    if mismatches:
        for table, col, actual, expected in mismatches:
            print(f"[!] {table}.{col} — found {actual}, expected {expected}")
    else:
        print(" All columns match expected types.")

if __name__ == "__main__":
    app()
