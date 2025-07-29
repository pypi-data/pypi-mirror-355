

def main(groups: list[str]) -> None:
  group_members = get_group_members(groups)

  all_usernames = {
    name for members in group_members.values() 
    for name in members
  }

  sorted_usernames = sorted(all_usernames)
  user_info_dict = {}
  failed_names = []

  for name in sorted_usernames:
    try:
      user_info = getpwnam(name)
      id_and_name = f"{user_info.pw_uid},{user_info.pw_gecos}"
      user_info_dict[name] = id_and_name
    except KeyError:
      failed_names.append(name)

  # Prepare CSV data
  header = ["username", "userid", "realname"] + groups
  rows = []

  for username in sorted_usernames:
    id_name = user_info_dict.get(username, "Unknown")

    userid, realname = id_name.split(",", 1)
    row = [username, userid, realname] + [1 if username in group_members[group] else 0 for group in groups]
    rows.append(row)

  # Write to CSV
  with open("group_members.csv", "w", newline="") as csvfile:
    writer = csv.writer(csvfile)
    writer.writerow(header)
    writer.writerows(rows)

  print("CSV file 'group_members.csv' generated successfully!")

if __name__ == "__main__":
  groups = ["bhklab", "radiomics", "bhklab_icb", "bhklab_pmcc_gyn_autosegmentation", "bhklab_pmcc_gyn_gu"]
  main(groups)

  try:
    import prettytable
  except ImportError:
    errmsg = (
      "PrettyTable module not found. "
      "This should be installed on H4H at /usr/lib/python3.9/site-packages/prettytable.py"
      "Otherwise please install it by running 'pip install prettytable'."
    )
    print(errmsg)
    exit()
  
  
  table = prettytable.from_csv(open("group_members.csv", "r"))

  # Shorten real names
  for row in table._rows:
    parts = row[2].split(" ")
    row[2] = f"{parts[0]} {parts[-1][0]}."

  new_header = []
  # shorten columns like bhklab_pmcc_gyn_autosegmentation into bhklab_pmcc_gyn_auto...
  for col in table._field_names:
    if len(col) > 20:
      name = col[:20] + "..."
    else:
      name = col
    new_header.append(name)
  
  table._set_field_names(new_header)

  print(table)


