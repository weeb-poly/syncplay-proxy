FROM python:3

# Set pip to have cleaner logs and no saved cache
ENV PIP_NO_CACHE_DIR=false \
    PIPENV_HIDE_EMOJIS=1 \
    PIPENV_IGNORE_VIRTUALENVS=1 \
    PIPENV_NOSPIN=1

# Install pipenv
RUN pip install -U pipenv

# Create the working directory
WORKDIR /app

# Copy Pipfiles
COPY Pipfile* ./

# Install project dependencies
RUN pipenv install --system --deploy

# Copy project files into working directory
# This is done last to prevent unnecessary image rebuilds
COPY . .

ENTRYPOINT ["python"]
CMD ["./syncplayProxy.py"]
