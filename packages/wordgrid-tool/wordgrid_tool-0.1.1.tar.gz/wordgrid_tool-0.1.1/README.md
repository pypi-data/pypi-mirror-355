# wordgrid-tool

A command-line tool to fetch stats and answers for the [Wordgrid](https://wordgrid.clevergoat.com/) game using its API.

With `wordgrid-tool`, you can get the following information for every square:
- How many answers exist
- How many answers have been found by players
- How many unicorns are in existence
- How many unicorns haven't been found yet
- (Optionally) Return a list of all the answers

---

## Installation

Make sure you have Python 3.7 or newer.

```bash
pip install wordgrid-tool
```

Or install from source:

```bash
git clone https://github.com/yourusername/wordgrid-tool.git
cd wordgrid-tool
pip install .
```

---

## Usage

```bash
wordgrid [OPTIONS]
```

### Options

| Flag           | Description                                                                 |
|----------------|-----------------------------------------------------------------------------|
| `-s`           | Specify the indices of the grid squares to check from 1-9. These are numbered from left to right, top to bottom. You can provide one or more (e.g. `-s 3, 7, 8`). |
| `-c`           | Specify the challenge number. You can use negative numbers to go backward, e.g. `-c -1` for yesterday's challenge. You can even look at challenges that haven't been revealed yet. |
| `--imacheater` | Returns all possible answers in the specified squares. |
| `--help`       | Show full CLI help message.                                                 |

---

## Examples

- Get stats for today's challenge:
  ```bash
  wordgrid
  ```

- Get stats for squares `3`, `7`, and `8` in today's challenge:
  ```bash
  wordgrid -s 3 7 8
  ```

- Get stats for day before yesterday's challenge:
  ```bash
  wordgrid -c -2
  ```

- Get all the answers for the specified squares:
  ```bash
  wordgrid -s 1 9 5 --imacheater
  ```

---

## Disclaimer

This tool uses publicly available data from the Wordgrid API and is not affiliated with or endorsed by the creators of Wordgrid. Use the `--imacheater` flag responsibly.

---

## License

MIT License — see the [LICENSE](LICENSE) file.

---

## Contributing

Issues and pull requests are welcome!