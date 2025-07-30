# swamp_mqtt_client/examples/basic.py

import asyncio

from dotenv import load_dotenv
import SwampClient as sc
import ProgressivePostgres as pp
from Zeitgleich import TimeSeriesData

load_dotenv()
logger = sc.setup_logger("MQTT_LOGGER_EXAMPLE")

def on_data(client, userdata, topic, payload: TimeSeriesData): # With MQTTCLIENT_AUTO_CONVERT_TS="true", payload is a TimeSeriesData object
    global db_client

    db_client.push_time_series_data(payload)

    logger.info(f"Received data: {payload}")
    
async def main():    
    global db_client

    db_client = pp.Client(name="TIMESCALE")
    
    mqtt_client = sc.MQTTClient(
        name="MQTT",
        on_data=on_data
    )

    try:
        await mqtt_client.run()
    except ConnectionError as e:
        logger.error(f"MQTT Client encountered a connection error: {e}")
    except Exception as e:
        logger.error(f"MQTT Client encountered an error: {e}")
    except KeyboardInterrupt:
        logger.info("MQTT client stopped manually.")
    finally:
        mqtt_client.disconnect()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("MQTT client stopped manually.")
