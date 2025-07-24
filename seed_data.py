from pymongo import MongoClient

client = MongoClient('mongodb://localhost:27017/')
db = client.college_voting

# Clear existing data
db.positions.delete_many({})
db.nominees.delete_many({})

# Insert positions
positions = [
    {"title": "President"},
    {"title": "Vice President"}
]

position_ids = db.positions.insert_many(positions).inserted_ids

# Insert nominees for President with image URLs
president_nominees = [
    {
        "name": "Alice",
        "position_id": str(position_ids[0]),
        "image_url": "https://randomuser.me/api/portraits/women/1.jpg"
    },
    {
        "name": "Bob",
        "position_id": str(position_ids[0]),
        "image_url": "https://randomuser.me/api/portraits/men/2.jpg"
    },
    {
        "name": "Mary",
        "position_id": str(position_ids[0]),
        "image_url": "https://randomuser.me/api/portraits/women/3.jpg"
    }
]

# Insert nominees for Vice President with image URLs
vice_president_nominees = [
    {
        "name": "Carol",
        "position_id": str(position_ids[1]),
        "image_url": "https://randomuser.me/api/portraits/women/4.jpg"
    },
    {
        "name": "Peter",
        "position_id": str(position_ids[1]),
        "image_url": "https://randomuser.me/api/portraits/men/5.jpg"
    },
    {
        "name": "John",
        "position_id": str(position_ids[1]),
        "image_url": "https://randomuser.me/api/portraits/men/6.jpg"
    }
]

db.nominees.insert_many(president_nominees)
db.nominees.insert_many(vice_president_nominees)

print("Database seeded with positions and nominees including image URLs.")
