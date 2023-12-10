FROM python:3.9-alpine

# Create a folder for the app
WORKDIR /bangla

# Install PostgreSQL dependencies
RUN apk add --no-cache postgresql-dev gcc musl-dev

# Install Daphne
RUN pip3 install daphne

# Create a group and add a user to the group
RUN addgroup systemUserGroup && adduser -D -G systemUserGroup developer

# Grant executable permissions to the group for the workdir
RUN chmod g+s /bangla

# Switch to the user
USER developer

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV SECRET_KEY=${SECRET_KEY}
ENV CLOUDINARY_CLOUD_NAME=${CLOUDINARY_CLOUD_NAME}
ENV CLOUDINARY_API_KEY=${CLOUDINARY_API_KEY}
ENV CLOUDINARY_API_SECRET=${CLOUDINARY_API_SECRET}
ENV EMAIL_HOST_USER=${EMAIL_HOST_USER}
ENV EMAIL_HOST_PASSWORD=${EMAIL_HOST_PASSWORD}
ENV DJANGO_SETTINGS_MODULE=${DJANGO_SETTINGS_MODULE}
ENV ADMIN_EMAIL=${ADMIN_EMAIL}
ENV ADMIN_PASSWORD=${ADMIN_PASSWORD}
ENV ADMIN_FULL_NAME=${ADMIN_FULL_NAME}
ENV ADMIN_PHONE_NUMBER=${ADMIN_PHONE_NUMBER}
ENV REDISCLOUD_URL=${REDISCLOUD_URL}
ENV DATABASE_URL=${DATABASE_URL}
ENV TREBLLE_API_KEY=${TREBLLE_API_KEY}
ENV TREBLLE_PROJECT_ID=${TREBLLE_PROJECT_ID}
ENV JWT_SECRET_KEY=${JWT_SECRET_KEY}

# Copy the requirements.txt file into the workdir
COPY ./requirements.txt requirements.txt

# Install the dependencies
RUN pip3 install -r requirements.txt

# Copy the Django project into the image
COPY . .

# collectstatic without interactive input, perform migrations and create a superuser automatically
CMD python3 manage.py migrate --settings=$DJANGO_SETTINGS_MODULE && \
    python3 manage.py createsu --settings=$DJANGO_SETTINGS_MODULE && \
    daphne -b 0.0.0.0 -p $PORT Bangla.asgi:application -v2
