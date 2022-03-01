FROM python:3.9.10-slim

COPY . /opt/project

WORKDIR /opt/project

RUN pip install -U pip && pip install -r requirements.txt
RUN tar -xzvf segmentation_maps.tar.gz --directory /

ENV PYTHONPATH="$PYTHONPATH:/opt/project"
EXPOSE 8501
ENTRYPOINT ["streamlit", "run", "--server.address=0.0.0.0", "src/app.py"]
