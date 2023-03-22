/*******************

  Create the schema

********************/

CREATE TABLE IF NOT EXISTS user (
  user_id SERIAL,
  password VARCHAR(255) NOT NULL,
  user_name VARCHAR(255) NOT NULL,
  email VARCHAR(255) UNIQUE NOT NULL,
  phone_number VARCHAR(20) UNIQUE NOT NULL,
  gender VARCHAR(6) CHECK(gender = 'male' or gender = 'female')
  age INTEGER,
  PRIMARY KEY(user_id, password)
);

CREATE TABLE IF NOT EXISTS property (
  property_id SERIAL PRIMARY KEY,
  owner_id INTEGER REFERENCES user (user_id) DEFERRABLE,
  address VARCHAR(255) UNIQUE NOT NULL,
  type VARCHAR(255) NOT NULL,
  num_rooms INTEGER NOT NULL,
  availability BOOLEAN DEFAULT TRUE,
  rate DECIMAL(10, 2) NOT NULL,
);

CREATE TABLE IF NOT EXISTS review (
  review_id SERIAL PRIMARY KEY,
  reviewer_id INTEGER REFERENCES user (user_id),
  property_id INTEGER REFERENCES property (property_id)
  rating INTEGER NOT NULL,
  review TEXT,
  review_date TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
);

CREATE TABLE IF NOT EXISTS booking (
  booking_ id SERIAL PRIMARY KEY,
  property_id INTEGER REFERENCES property (property_id),
  student_id INTEGER REFERENCES user (user_id),
  start_date DATE NOT NULL,
  end_date DATE NOT NULL,
  booking_date TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
  status VARCHAR(16) CHECK(status = 'processing', status = 'confirmed')
);


CREATE TABLE IF NOT EXISTS transaction (
  transaction_id SERIAL PRIMARY KEY,
  booking_id INTEGER REFERENCES bookings (booking_id),
  amount DECIMAL(10, 2) NOT NULL,
  status ENUM('pending', 'completed', 'refunded', 'disputed') NOT NULL,
  datetime TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
);

CREATE TABLE IF NOT EXISTS administrator (
  user_id INTEGER,
  password VARCHAR(256),
  permissions TEXT
  PRIMARY KEY(user_id, password)
  FOREIGN KEY(user_id, password) REFERENCES user (user_id, password)
);

	
	
	
);

