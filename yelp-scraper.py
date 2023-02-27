
import requests
import json
import pandas as pd

# Set the API endpoint and parameters
url = 'https://api.yelp.com/v3/businesses/search'
headers = {'Authorization': 'Bearer 9akq64ELYzghN_aZOjDzkgO-SoC_jnrRrbOn9gUE8RrLEMPutJQ-QZPXQVUbQAW1omsIA4rXZlrbqlP2ShJWBqrlCMdjEdAeL9VDkWaCvPRp9aqYfJ0kmD4-seb6Y3Yx'}
location = 'Manhattan'
cuisine_types = ['mexican', 'italian', 'korean', 'indian', 'chinese']
#offsets = [ x*20 +1 for x in range(50)]
offsets = [ x*20 +1 for x in range(49)]
output = []

# Make the API request for each cuisine type
for cuisine_type in cuisine_types:
    restaurants = []

    for offset in offsets:
        params = {'term': cuisine_type + ' restaurants', 'location': location, 'offset': offset}
        response = requests.get(url, headers=headers, params=params)
        data = json.loads(response.text)
        businesses = data['businesses']
        restaurants += businesses


    df = pd.DataFrame(restaurants)
    df1 = df[['id', 'name', 'location', 'coordinates', 'review_count', 'rating']]

    df1['zip_code'] = df1['location'].apply(lambda x: x['zip_code'])
    df1['location'] = df1['location'].apply(lambda x: x['address1'])
    df1['rating'] = df1['rating'].apply(lambda x: str(x))
    df1['cuisine'] = [cuisine_type] * len(df1['location'])

    for val in df1['coordinates']:
        val['latitude'] = str(val['latitude'])
        val['longitude'] = str(val['longitude'])

    df_dict = df1.to_dict(orient='records')


    for record in df_dict:
        output.append(record)


# Output data
output_formatted = ''
for i, item in enumerate(output):
    output_formatted += '{"index": {"_index": "restaurants", "_id": "%s"}}\n' % item['id']
    output_formatted += json.dumps({'id': item['id'], 'cuisine': item['cuisine']})
    output_formatted += 'output_formatted'




# Print output
print(output_formatted)


text_file = open("Output.txt", "w")

text_file.write(output_formatted)

text_file.close()



with open('yelp_data_elastic_search.json', 'w') as outfile:
    json.dump(output_formatted, outfile)
