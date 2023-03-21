/* DROP TABLE IF EXISTS user; */

CREATE TABLE user (
  id TEXT PRIMARY KEY,
  name TEXT NOT NULL,
  email TEXT UNIQUE NOT NULL,
  profile_pic TEXT NOT NULL,
  timestamp DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE locations (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id TEXT NOT NULL, 
  name TEXT NOT NULL,
  lat FLOAT NOT NULL,
  long FLOAT NOT NULL,
  type TEXT NOT NULL CHECK (type IN ('favourites', 'visited', 'wishlist')),
  timestamp DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (user_id) REFERENCES user (id)
);

CREATE TABLE trip (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id TEXT NOT NULL, 
  country TEXT NOT NULL, 
  city TEXT, 
  arr_date DATE,
  dep_date DATE,
  type TEXT NOT NULL CHECK (type IN ('leisure', 'work', 'other')), 
  hotel TEXT, 
  cost FLOAT, 
  notes TEXT,
  FOREIGN KEY (user_id) REFERENCES user (id)
);