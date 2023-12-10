# ADConnectAPI - Advertisement and Matrimonial Connection API

![logo-icon.png](static%2Flogo-icon.png)

<a href="https://www.flaticon.com/free-icons/adwords" title="adwords icons">Adwords icons created by Freepik - Flaticon</a>

Facilitate seamless advertisement posting for events, perform CRUD operations, create matrimonial profiles, and connect
with people using our API - ADConnectAPI.

## AdConnect API Link

https://pay-trac.vercel.app/

## Table of Contents

- [Introduction](#adconnectapi---advertisement-and-matrimonial-connection-api)
- [Key Features](#key-features)
- [Testing](#testing)
- [Additional Tips](#additional-tips)
- [Getting Started](#getting-started)

## Key Features

1. **Advertisement Management:** Simplify the process of posting and managing ads for events. Admin approval ensures
   quality ads.
2. **Matrimonial Profiles:** Create detailed matrimonial profiles and connect with potential partners.
3. **Real-Time Chat:**  Engage in real-time chat for both advertisement and matrimonial connections.
4. **Connection Requests:** Allow users to send and receive connection requests for events or matrimonial profiles.
5. **Favorite Listings:** Save and organize favorite ads and matrimonial profiles for quick access.
6. **Filtering Options:** Efficiently filter ads and profiles based on user preferences.

## Testing

- Seamless advertisement posting and management
- Successful creation and connection of matrimonial profiles
- Reliable real-time chat functionality
- Admin approval for quality ads
- Connection request handling
- Favorite ads and profiles feature
- Advanced filtering options

## Technologies used for API

- Python
- Django, Django Rest Framework
- SQLite3, PostgreSQL
- Docker and Docker-Compose
- Railway for deployment
- Neon.tech for database
- Cloudinary
- Gmail for free email

## Getting Started

Follow these steps to get the project up and running on your local machine:

1. Clone the repository:
    ```
    git clone https://github.com/S13G/AdConnect.git
   ```
2. Navigate to the project directory:
   ```
    cd AdConnect
   ```
3. Rename the ``.env.template`` to ``.env`` and update the values.


4. Build and run the service with
   ```
   docker-compose up --build
   ```
   or execute the command below in case permission is denied and root user/permission is needed
   ```
   sudo docker-compose up --build
   ```
   The service will build and run on port ``8000``


5. Launch a new terminal session and run the following commands(if you are not using docker, but for
   caution: `run them`)
   ```
   django mm
   ```
   The command above runs the migrations if there are some unapplied migrations
   ```
   django m
   ```
   The command above performs the database migrations


6. Create an admin user with the command below(make sure you fill in the admin details in the env):
   ```
   django createsu
   ```
   After creating the superuser, access the admin panel and login with your admin credentials with the
   link https://localhost:8000/admin/

   ### Admin Login Screen

   ![img1.png](static%2Fimg1.png)

   ### Admin Dashboard Screens (Has both Light and Dark Modes)

   ![img2.png](static%2Fimg2.png)


7. Add your data through the swagger doc and you can download the schema and import it into your postman collection
