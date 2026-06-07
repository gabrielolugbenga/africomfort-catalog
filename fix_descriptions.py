import csv
import io

with open('catalog.csv', 'r') as f:
    content = f.read()

lines = content.strip().split('\n')
header = lines[0]
new_lines = [header]

for line in lines[1:]:
    reader = csv.reader(io.StringIO(line))
    row = next(reader)
    if len(row) >= 3:
        title = row[1].strip('"')
        # Capitalize first letter only for description
        description = title.capitalize()
        row[2] = description
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(row)
        new_lines.append(output.getvalue().strip())

with open('catalog.csv', 'w') as f:
    f.write('\n'.join(new_lines))

print('Done')
