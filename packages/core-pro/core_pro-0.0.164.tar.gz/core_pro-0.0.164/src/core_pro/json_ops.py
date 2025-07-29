import orjson
from pathlib import Path
import polars as pl
from tqdm.auto import tqdm


class JsonETL:
    def __init__(self, files: list[Path]):
        self.files = files

    @classmethod
    def from_path(cls, path: Path, folder: str):
        files = sorted(
            [*path.glob(f"{folder}/*.json")], key=lambda x: int(x.stem.split("_")[-1])
        )
        print(f"[JsonETL] Found {len(files)} json files in {folder}")
        return cls(files)

    @staticmethod
    def write_orjson(data, path: Path, file_name: str):
        # config
        json_options = orjson.OPT_NAIVE_UTC | orjson.OPT_INDENT_2
        json_bytes = orjson.dumps(data, option=json_options)

        # export
        path.mkdir(parents=True, exist_ok=True)
        (path / f"{file_name}.json").write_bytes(json_bytes)

    @staticmethod
    def parse_string_to_orjson(string_inputs: list[str]) -> list[dict]:
        parsed_list = []
        for s in tqdm(string_inputs, desc="[JSON] Parsing"):
            if isinstance(s, list):
                s = s[0]
            start = s.find("{")
            end = s.rfind("}") + 1
            if start != -1 and end != 0:
                try:
                    parsed_list.append(orjson.loads(s[start:end]))
                except orjson.JSONDecodeError:
                    parsed_list.append({})
        return parsed_list

    @staticmethod
    def wrap_values_in_list(item: dict) -> dict:
        for key, value in item.items():
            if not isinstance(value, list):
                item[key] = [value]
            else:
                item[key] = [
                    item
                    for sublist in value
                    if sublist
                    for item in (sublist if isinstance(sublist, list) else [sublist])
                ]
        return item

    def load_json(self) -> dict:
        list_json = [
            orjson.loads(open(str(i), "r").read())
            for i in tqdm(self.files, desc="[JsonETL] Loading in folder")
        ]
        list_json = sum(list_json, [])  # flatten list
        return list_json

    def pipe_to_df(self, col: str = "response") -> pl.DataFrame:
        # load
        lst = self.load_json()
        df_json = pl.DataFrame(lst)

        # json -> dict
        lst_response = JsonETL.parse_string_to_orjson(df_json[col].to_list())
        lst_response = [JsonETL.wrap_values_in_list(i) for i in lst_response]

        df_response = pl.DataFrame(lst_response, strict=False)
        df_process = pl.concat([df_json.drop([col]), df_response], how="horizontal")
        return df_process
