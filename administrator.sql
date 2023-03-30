INSERT INTO users(user_id,password_hash,user_name,email,phone_number,gender,age) VALUES (9999,'admin_password','group5_admin','group5_admin@nus.edu','995','male',23);

/* populate administrators */

INSERT INTO administrator (user_id, password_hash, permissions) VALUES (9999, 'admin_password', 'ACCESS TO ADMIN DASHBOARD, ACCESS TO ALL TABLES, ACCESS TO DATABASE')