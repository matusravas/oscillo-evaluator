FROM python:3.12.3

# Set the working directory in the container
WORKDIR /oscillo-evaluator

# Copy the requirements file into the container
COPY requirements.txt /oscillo-evaluator/requirements.txt

# Install any dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Install vim
RUN apt-get update && apt-get install -y vim

# Copy all files and directories to the container
COPY . /oscillo-evaluator

# Install Gunicorn
RUN pip install gunicorn

# Expose port 5009 for the application to run on SSL
EXPOSE 5009

CMD ["gunicorn", "-w", "9", "-b", "0.0.0.0:5009", "main:app"]
