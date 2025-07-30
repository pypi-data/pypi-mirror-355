import argparse
import datetime
import requests
import json


def main():
    # Get the number of the current challenge from the current day (This will be wrong if there's ever a day that the wordgrid is not updated)
    now = datetime.datetime.today()
    day = datetime.datetime(
        2024, 5, 31
    )  # Assumed to be the day of the first wordgrid since 13/6/2025 is the 378th challenge
    game_number = (now - day).days

    # Parse any command line arguments
    parser = argparse.ArgumentParser(
        description="A command-line tool to fetch stats and answers for the Wordgrid game (https://wordgrid.clevergoat.com/) using its API."
    )
    parser.add_argument(
        "-s",
        nargs="+",
        help="(Required) Select squares to look at, squares are numbered 1-9 from left to right, top to bottom",
    )
    parser.add_argument(
        "-c",
        help=f"(Optional) Select the game number (0-{game_number}), minus values allow you to go backwards",
    )
    parser.add_argument(
        "--imacheater",
        action="store_true",
        help="(Optional) Show all the answers for the squares selected (Warning: you may not be able to see all the answers if the list is long enough)",
    )
    args = parser.parse_args()

    # 0-index and range check the -s argument
    if args.s == None:
        squares = [i for i in range(9)]
    else:
        squares = [int(square) - 1 for square in args.s]
        for square in squares:
            if square < 0 or square > 8:
                print(
                    f"Square {square + 1} does not exist, please choose squares between 1-9"
                )
                exit()

    # Handle a possible -c argument
    c = None
    if args.c != None:
        c = int(args.c)

    if c:
        # Range checking
        if c > game_number:
            print(
                f"Challenge {c} may or may not exist yet, pick a challenge in [-{game_number}, {game_number}]"
            )
        if c < -game_number:
            print(
                f"Challenge {game_number + c} doesn't exist, pick a challenge in [-{game_number}, {game_number}]"
            )
            exit()

        # Parse positive and negative values
        if c < 0:
            game_number += c
        else:
            game_number = c

    # Request challenge data from the API and read the json as a dictionary
    response = requests.get(f"https://api.clevergoat.com/wordgrid/game/{game_number}")
    try:
        data = json.loads(response.text)
    except:
        print("Failed to read game data")
        exit()

    # Check that we have the correct game
    if data["gameNumber"] != game_number:
        print(
            f"This is not game {game_number}, this is game {data["gameNumber"]}. Please report this error."
        )

    # Loop over each square selected and add parsed data to the printed output
    printed_output = ""
    printed_output += f"Game {data["gameNumber"]}:\n"
    for square in squares:
        # Get the stats
        answers = len(data["squares"][square]["answers"])
        unicorns = int(data["squares"][square]["currentUnicorns"])
        unfound_unicorns = int(data["squares"][square]["unfoundUnicorns"])
        words_found = answers - unfound_unicorns

        # Get the name and rule for the current square from its index
        rules = ""
        rules += data["rows"][square // 3]["text"] + " and "
        rules += data["columns"][square % 3]["text"].lower()

        square_name = ""
        # Find the row
        match square // 3:
            case 0:
                square_name += "Top "
            case 1:
                square_name += "Middle "
            case 2:
                square_name += "Bottom "

        # Find the column
        match square % 3:
            case 0:
                square_name += "left"
            case 1:
                square_name += "middle"
            case 2:
                square_name += "right"

        # Format the printed output
        printed_output += f"{square_name} square\n"
        printed_output += f"Rules: {rules}\n"
        printed_output += f"Found: {words_found} out of {answers} ({100 * (words_found / answers)}%)\n"
        printed_output += f"{answers} possible answers, {unicorns} current unicorns and {unfound_unicorns} unfound unicorns\n"

        if args.imacheater:
            printed_output += f"{data["squares"][square]["answers"]}\n"

        printed_output += "\n"

    # Trim trailing newline
    print(printed_output[:-2])


if __name__ == "__main__":
    main()
