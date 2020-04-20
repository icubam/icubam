from absl import app
from absl import flags
import pandas as pd
import json
from icubam.db import synchronizer

flags.DEFINE_string(
  "input", None, "Path to input csv file containing ICU data."
)
flags.DEFINE_string("output", None, "Path to output csv file.")
flags.DEFINE_string(
  "finess_geojson", "resources/finess.geojson",
  "Path to geojson file containing FINESS data."
)
flags.DEFINE_string(
  "fr_cities", "resources/fr_cities.csv",
  "Path to csv file containing french cities data."
)

FLAGS = flags.FLAGS

finess_df = None
cities_df = None


def update_val(row):

  if not row.legal_id:
    print(f"Missing legal id for {row.name}. Skipping.")
    return row

  if not row.country:
    print(f"Missing country code for {row.name}. Skipping.")
    return row

  if row.country == "FR":
    print(f"Looking up {row.legal_id}")
    finess_row_df = finess_df.loc[finess_df["properties.nofinesset"] ==
                                  row.legal_id]

    if finess_row_df.empty:
      print(f"Could not find FINESS {row.legal_id}. Skipping.")
      return row

    coords = finess_row_df["geometry.coordinates"].values[0]
    departement = finess_row_df["properties.departement"].values[0]
    city = int(finess_row_df["properties.commune"].values[0])
    city_code = f"{departement}{city:03d}"
    city_row_df = cities_df.loc[cities_df["com"] == city_code]
    city_name = city_row_df["nccenr"].values[0]
    if row.lat is None:
      row.lat = coords[1]
    if row.long is None:
      row.long = coords[0]
    if row.city is None:
      row.city = city_name

  return row


def main(args=None):
  global finess_df
  global cities_df

  print(f"Loading FINESS data from: {FLAGS.finess_geojson}")
  finess_contents = open(FLAGS.finess_geojson, "r", encoding="utf-8")
  finess_df = pd.json_normalize(json.load(finess_contents))
  assert finess_df.shape[1] > 1

  print(f"Loading cities data from: {FLAGS.fr_cities}")
  cities_content = open(FLAGS.fr_cities, "r", encoding="utf-8")
  cities_df = pd.read_csv(cities_content)
  print(cities_df)

  print(f"Loading ICU CSV from: {FLAGS.input}")
  with open(FLAGS.input) as icus_f:
    icus_df = pd.read_csv(icus_f, dtype=synchronizer.ICU_DTYPE)
    col_diff = set(synchronizer.ICU_COLUMNS) - set(icus_df.columns)
    if len(col_diff) > 0:
      raise ValueError(f"Missing columns in input data: {col_diff}.")

  icus_df = icus_df.replace({pd.NA: None})

  output_df = icus_df.apply(update_val, axis=1)

  output_csv = output_df.to_csv(index=False)

  with open(FLAGS.output, 'w') as f_out:
    f_out.write(output_csv)


if __name__ == "__main__":
  flags.mark_flag_as_required('input')
  flags.mark_flag_as_required('output')
  app.run(main)
