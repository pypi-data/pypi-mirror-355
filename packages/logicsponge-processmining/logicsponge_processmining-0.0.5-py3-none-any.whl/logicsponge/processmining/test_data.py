"""Test data for process mining."""

import logging
from collections import defaultdict
from collections.abc import Iterator
from pathlib import Path
from typing import Any

import pandas as pd

from logicsponge.processmining.automata import PDFA
from logicsponge.processmining.config import DEFAULT_CONFIG
from logicsponge.processmining.data_utils import FileHandler, handle_keys, interleave_sequences, parse_timestamp
from logicsponge.processmining.types import Event, StateId

logger = logging.getLogger(__name__)

FOLDERNAME = "data"
file_handler = FileHandler(folder=FOLDERNAME)

stop_symbol = DEFAULT_CONFIG["stop_symbol"]

DATA = "file"
# DATA = "synthetic"
# DATA = "PDFA"


def csv_row_iterator(
    file_path: str, delimiter: str = ",", chunksize: int = 1000, dtypes: dict[str, str] | None = None
) -> Iterator[dict[str, Any]]:
    """
    Create an iterator that yields rows from a large CSV file.

    Args:
        file_path (str): Path to the CSV file.
        delimiter (str): The delimiter.
        chunksize (int): Number of rows to read at a time.
        dtypes (dict[str, str] | None): Dictionary of column names and their data types.

    Yields:
        NamedTuple: Each row as a nametuple of column names to values.

    """
    # by default everything is a str, unless explicitely specified.
    if dtypes is None:
        dtypes = {}
    all_dtypes: defaultdict[str, str] = defaultdict(lambda: "string", **dtypes)

    # using keep_default_na=False to not convert "na" to float('nan') but keep it as a str
    chunk_iter = pd.read_csv(
        file_path, chunksize=chunksize, delimiter=delimiter, dtype=all_dtypes, keep_default_na=False
    )
    for chunk in chunk_iter:
        yield from chunk.to_dict("records")


# ============================================================
# Data collection
# ============================================================

data_collection = {
    "BPI_Challenge_2011": {
        "url": "https://data.4tu.nl/file/5ea5bb88-feaa-4e6f-a743-6460a755e05b/6f9640f9-0f1e-44d2-9495-ef9d1bd82218",
        "doi": "10.4121/uuid:d9769f3d-0ab0-4fb8-803b-0d1120ffcf54",
        "filetype": "xes.gz",
        "target_filename": "BPI_Challenge_2011.csv",
        "case_keys": ["case:concept:name"],
        "activity_keys": ["concept:name"],
        "timestamp": "time:timestamp",
        "delimiter": ",",
        "dtypes": None,
    },
    "BPI_Challenge_2012": {
        "url": "https://data.4tu.nl/file/533f66a4-8911-4ac7-8612-1235d65d1f37/3276db7f-8bee-4f2b-88ee-92dbffb5a893",
        "doi": "10.4121/uuid:3926db30-f712-4394-aebc-75976070e91f",
        "filetype": "xes.gz",
        "target_filename": "BPI_Challenge_2012.csv",
        "case_keys": ["case:concept:name"],
        "activity_keys": ["concept:name"],
        "timestamp": "time:timestamp",
        "delimiter": ",",
        "dtypes": None,
    },
    "BPI_Challenge_2013": {
        "url": "https://data.4tu.nl/file/0fc5c579-e544-4fab-9143-fab1f5192432/aa51ffbb-25fd-4b5a-b0b8-9aba659b7e8c",
        "doi": "10.4121/uuid:500573e6-accc-4b0c-9576-aa5468b10cee",
        "filetype": "xes.gz",
        "target_filename": "BPI_Challenge_2013.csv",
        "target_foldername": "data",
        "case_keys": ["case:concept:name"],
        "activity_keys": ["lifecycle:transition"],
        "timestamp": "time:timestamp",
        "delimiter": ",",
        "dtypes": None,
    },
    "BPI_Challenge_2014": {
        "url": "https://data.4tu.nl/file/657fb1d6-b4c2-4adc-ba48-ed25bf313025/bd6cfa31-44f8-4542-9bad-f1f70c894728",
        "doi": "10.4121/uuid:86977bac-f874-49cf-8337-80f26bf5d2ef",
        "filetype": "csv",
        "target_filename": "BPI_Challenge_2014.csv",
        "target_foldername": "data",
        "case_keys": ["Incident ID"],
        "activity_keys": ["IncidentActivity_Type"],
        "timestamp": "DateStamp",
        "sort_by_time": "DateStamp",
        "delimiter": ";",
        "dtypes": None,
    },
    "BPI_Challenge_2017": {
        "url": "https://data.4tu.nl/file/34c3f44b-3101-4ea9-8281-e38905c68b8d/f3aec4f7-d52c-4217-82f4-57d719a8298c",
        "doi": "10.4121/uuid:5f3067df-f10b-45da-b98b-86ae4c7a310b",
        "filetype": "xes.gz",
        "target_filename": "BPI_Challenge_2017.csv",
        "target_foldername": "data",
        "case_keys": ["case:concept:name"],
        "activity_keys": ["concept:name"],
        "timestamp": "time:timestamp",
        "delimiter": ",",
        "dtypes": None,
    },
    "BPI_Challenge_2018": {
        "url": "https://data.4tu.nl/file/443451fd-d38a-4464-88b4-0fc641552632/cd4fd2b8-6c95-47ae-aad9-dc1a085db364",
        "doi": "10.4121/uuid:3301445f-95e8-4ff0-98a4-901f1f204972",
        "filetype": "xes.gz",
        "target_filename": "BPI_Challenge_2018.csv",
        "target_foldername": "data",
        "case_keys": ["case:concept:name"],
        "activity_keys": ["concept:name"],
        "timestamp": "time:timestamp",
        "delimiter": ",",
        "dtypes": None,
    },
    "BPI_Challenge_2019": {
        "url": "https://data.4tu.nl/file/35ed7122-966a-484e-a0e1-749b64e3366d/864493d1-3a58-47f6-ad6f-27f95f995828",
        "doi": "10.4121/uuid:d06aff4b-79f0-45e6-8ec8-e19730c248f1",
        "filetype": "xes",
        "target_filename": "BPI_Challenge_2019.csv",
        "case_keys": ["case:Purchasing Document", "case:Item"],
        "activity_keys": ["concept:name"],
        "timestamp": "time:timestamp",
        "delimiter": ",",
        "dtypes": None,
    },
    "Sepsis_Cases": {
        "url": "https://data.4tu.nl/file/33632f3c-5c48-40cf-8d8f-2db57f5a6ce7/643dccf2-985a-459e-835c-a82bce1c0339",
        "doi": "10.4121/uuid:915d2bfb-7e84-49ad-a286-dc35f063a460",
        "filetype": "xes.gz",
        "target_filename": "Sepsis_Cases.csv",
        "case_keys": ["case:concept:name"],
        "activity_keys": ["concept:name"],
        "timestamp": "time:timestamp",
        "delimiter": ",",
        "dtypes": None,
    },
    "Synthetic_Train": {
        "url": None,
        "doi": None,
        "filetype": None,
        "target_filename": "Synthetic_Train.csv",
        "case_keys": ["case:concept:name"],
        "activity_keys": ["concept:name"],
        "timestamp": "time:timestamp",
        "delimiter": ",",
        "dtypes": None,
    },
    "Synthetic_Test": {
        "url": None,
        "doi": None,
        "filetype": None,
        "target_filename": "Synthetic_Test.csv",
        "case_keys": ["case:concept:name"],
        "activity_keys": ["concept:name"],
        "timestamp": "time:timestamp",
        "delimiter": ",",
        "dtypes": None,
    },
    "Helpdesk": {
        "url": "https://data.4tu.nl/file/94ee26c8-78f6-4387-b32b-f028f2103a2c/697ff9af-fca0-4363-bd84-e81735d27e9f",
        "doi": "10.4121/uuid:0c60edf1-6f83-4e75-9367-4c63b3e9d5bb",
        "filetype": "csv",
        "target_filename": "Helpdesk.csv",
        "case_keys": ["Case ID"],
        "activity_keys": ["Activity"],
        "timestamp": "Complete Timestamp",
        "sort_by_time": "Complete Timestamp",
        "delimiter": ",",
        "dtypes": None,
    },
}


# ============================================================
# File data loader
# ============================================================

if DATA == "file":
    # data_name = "Synthetic_Train"

    data_name = "Sepsis_Cases"

    # data_name = "Helpdesk"
    # data_name = "BPI_Challenge_2013" # 2014 2017
    # data_name = "BPI_Challenge_2017"

    # =========================================================
    # DEFAULT DATA (= train set, when synthetic)
    # =========================================================

    mydata = data_collection[data_name]
    file_path = Path(FOLDERNAME) / mydata["target_filename"]

    mydata["file_path"] = file_path
    if mydata["url"] is not None:
        file_handler.handle_file(
            file_type=mydata["filetype"], url=mydata["url"], filename=mydata["target_filename"], doi=mydata["doi"]
        )
    row_iterator = csv_row_iterator(
        file_path=mydata["file_path"], delimiter=mydata["delimiter"], dtypes=mydata["dtypes"]
    )

    # =========================================================
    # ADDITIONAL DATA (= test set, when synthetic)
    # =========================================================

    data_name_test = data_name.replace("Train", "Test")
    mydata_test = data_collection[data_name_test]
    file_path = Path(FOLDERNAME) / mydata_test["target_filename"]
    mydata_test["file_path"] = file_path
    row_iterator_test = csv_row_iterator(
        file_path=mydata_test["file_path"], delimiter=mydata_test["delimiter"], dtypes=mydata_test["dtypes"]
    )

    # Sort by timestamp if "sort_by_time" is defined
    # if "sort_by_time" in data and data["sort_by_time"]:
    #     timestamp_column = data["sort_by_time"]
    #     if timestamp_column in csv_file.columns:
    #         # Convert the timestamp column to datetime format
    #         csv_file[timestamp_column] = pd.to_datetime(csv_file[timestamp_column], format='%d-%m-%Y %H:%M:%S',
    #                                                     errors='coerce')
    #
    #         # Check for any invalid datetime values (NaT) after conversion
    #         if csv_file[timestamp_column].isna().any():
    #             raise ValueError(
    #                 f"Invalid datetime format in column '{timestamp_column}'. Ensure format '%d-%m-%Y %H:%M:%S'.")
    #
    #         # Sort the DataFrame by the timestamp column
    #         csv_file.sort_values(by=timestamp_column, inplace=True)
    #     else:
    #         raise KeyError(f'Timestamp column "{timestamp_column}" not found in the CSV file.')

    dataset: Iterator[Event]
    dataset_test: Iterator[Event]

    def my_iterator(iter_data: dict, iter_row_iterator: Iterator) -> Iterator[Event]:
        """Create an iterator that yields events from a large CSV file."""
        timestamp_key = iter_data.get("timestamp")  # Check if timestamp key is defined
        for row in iter_row_iterator:
            # Create the Event dictionary
            event: Event = {
                "case_id": handle_keys(iter_data["case_keys"], row),  # Extract case ID
                "activity": handle_keys(iter_data["activity_keys"], row),  # Extract activity
                "timestamp": None,
            }

            # Handle timestamp if the key is provided
            if timestamp_key:
                raw_timestamp = row.get(timestamp_key)
                if raw_timestamp:
                    try:
                        # Parse timestamp; customize format if necessary
                        # parsed_timestamp = datetime.fromisoformat(raw_timestamp)
                        parsed_timestamp = parse_timestamp(raw_timestamp)
                    except ValueError:
                        # Handle invalid timestamps by assigning a default value
                        parsed_timestamp = None
                    event["timestamp"] = parsed_timestamp  # Add timestamp to event

            yield event

    dataset = my_iterator(mydata, row_iterator)
    dataset_test = my_iterator(mydata_test, row_iterator_test)


# ============================================================
# Synthetic data sets
# ============================================================

if DATA == "synthetic":
    sequences = []

    # Open the file and process it line by line
    with Path(
        "/Users/bollig/innatelogic/git/circuits/innatelogic/circuits/process_mining/data/10.pautomac.train"
    ).open() as file:
        # Skip the first line (a header)
        next(file)

        # Process each line to extract the sequences
        for line in file:
            # Split the line into individual string numbers and convert them to integers
            numbers = list(map(int, line.split()))

            # Ignore the first element of each line
            if len(numbers) > 1:
                # As 0 is padding symbol in LSTMs, add 1 to each number in the sequence after ignoring the first element
                incremented_numbers = [num + 1 for num in numbers[1:]]

                # Store the modified sequence
                sequences.append([*incremented_numbers, stop_symbol])

    dataset = iter(interleave_sequences(sequences, random_index=False))


# ============================================================
# PDFA simulation
# ============================================================


if DATA == "PDFA":
    pdfa = PDFA()

    pdfa.add_activities(["init", "a", "b"])

    pdfa.create_states(2)
    pdfa.set_initial_state(StateId(0))

    pdfa.transitions[StateId(0)]["init"] = 1
    pdfa.transitions[StateId(1)]["a"] = 1
    pdfa.transitions[StateId(1)]["b"] = 1

    pdfa.set_probs(StateId(0), {stop_symbol: 0.0, "init": 1.0, "a": 0.0, "b": 0.0})
    pdfa.set_probs(StateId(1), {stop_symbol: 0.01, "init": 0.0, "a": 0.495, "b": 0.495})

    dataset = iter(interleave_sequences(pdfa.simulate(100000)))
