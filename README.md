# Dweed - Dweet.io discovery library and prtotocol

Requires python 3.

## Example

0. Install pre-requisites.
   ```
   $ pip install bokeh
   ```

1. Create unique id for discovery service.
   ```
   $ uuidgen
   4c402fd7-819a-4625-9ff6-fd57a11ab6d9
   ```

2. Run kind-of-a-sensor.
   ```
   $ python sensor_example.py 4c402fd7-819a-4625-9ff6-fd57a11ab6d9
   ```

3. While sensor is running, start view example from other terminal or machine.
   ```
   python view_example.py  4c402fd7-819a-4625-9ff6-fd57a11ab6d9   
   ```

4. Browser should open automatically, displaying real-time data. If not, open link noted below.
   ```
   http://localhost:5006/
   ```
