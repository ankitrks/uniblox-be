# Use an official Python runtime as a parent image
FROM python:3.8

# Set the working directory to /ecommerce_backend
WORKDIR /ecommerce_backend

# Copy the current directory contents into the container at /ecommerce_backend
COPY . /ecommerce_backend

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Make port 8000 available to the world outside this container
EXPOSE 8000

# Run app.py when the container launches
CMD ["python", "manage.py", "loaddata", "store/fixtures/products_fixture.json"]
CMD ["python", "manage.py", "migrate"]
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
