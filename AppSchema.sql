/*******************

  Create the schema

********************/

/*
DROP TABLE administrator;
DROP TABLE review;
DROP TABLE transaction;
DROP TABLE booking;
DROP TABLE property;
DROP TABLE users;
*/

CREATE TABLE IF NOT EXISTS users (
  user_id INTEGER PRIMARY KEY,
  password_hash VARCHAR(255) NOT NULL,
  user_name VARCHAR(255) NOT NULL,
  email VARCHAR(255) UNIQUE NOT NULL,
  phone_number VARCHAR(20) UNIQUE NOT NULL,
  gender VARCHAR(6) CHECK(gender = 'male' or gender = 'female'),
  age INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS property (
  property_id INTEGER PRIMARY KEY,
  owner_id INTEGER REFERENCES users(user_id),
  address VARCHAR(255) NOT NULL,
  property_type VARCHAR(255) NOT NULL,
  num_rooms INTEGER NOT NULL,
  availability VARCHAR(3) CHECK(availability = 'yes' OR availability = 'no'),
  room_rate INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS review (
  review_id INTEGER PRIMARY KEY,
  reviewer_id INTEGER REFERENCES users (user_id),
  property_id INTEGER REFERENCES property (property_id),
  rating INTEGER NOT NULL,
  review TEXT,
  review_date TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS booking (
  booking_id INTEGER PRIMARY KEY,
  property_id INTEGER REFERENCES property (property_id),
  student_id INTEGER REFERENCES users (user_id),
  start_date DATE NOT NULL,
  end_date DATE NOT NULL,
  booking_date TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  status VARCHAR(16) CHECK(status = 'processing' OR status = 'confirmed')
);

CREATE TABLE IF NOT EXISTS transaction (
  transaction_id INTEGER PRIMARY KEY,
  booking_id INTEGER REFERENCES booking (booking_id),
  amount DECIMAL(10, 2) NOT NULL,
  status VARCHAR CHECK(status = 'processing' OR status = 'paid'),
  datetime TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS administrator (
  user_id INTEGER,
  password_hash VARCHAR(256),
  permissions TEXT,
  PRIMARY KEY(user_id),
  FOREIGN KEY(user_id) REFERENCES users (user_id)
);
