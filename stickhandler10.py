#!/usr/bin/env python3
"""
StickHandler Pro — Raspberry Pi-only starter for a 10-LED / 10-Hall-sensor build.

IMPORTANT:
- This is a new, simplified game loop, NOT the original hockey1.py.
- Connect each Hall sensor's digital output to a Pi GPIO only if its output is
  confirmed to be 3.3 V-safe. Never feed 5 V into a Raspberry Pi GPIO.
- Edit LED_PINS and SENSOR_PINS to match your actual wiring (BCM GPIO numbers).
- GPIO numbers here are examples only; check your wiring before powering on.
- Uses gpiozero, normally included with Raspberry Pi OS.
"""

from time import monotonic, sleep
from random import choice
import signal
import sys

from gpiozero import LED, Button

# BCM GPIO numbers — EXAMPLE PINOUT ONLY. Change these to match your build.
# Ten LEDs:
LED_PINS = [4, 17, 27, 22, 5, 6, 13, 19, 26, 21]
# Ten Hall sensor digital outputs:
SENSOR_PINS = [10, 9, 11, 0, 1, 7, 8, 12, 16, 20]

ROUND_SECONDS = 45
DEBOUNCE_SECONDS = 0.08
START_DELAY_SECONDS = 2

# Many digital Hall modules pull D0 LOW when triggered.
# If your sensors go HIGH when a magnet is detected, change to True.
SENSOR_ACTIVE_HIGH = False


def main():
    leds = []
    sensors = []
    score = 0
    hits = 0
    target = None
    last_hit_time = 0.0
    running = True

    try:
        leds = [LED(pin) for pin in LED_PINS]
        sensors = [
            Button(
                pin,
                pull_up=not SENSOR_ACTIVE_HIGH,
                bounce_time=DEBOUNCE_SECONDS,
                active_state=SENSOR_ACTIVE_HIGH,
            )
            for pin in SENSOR_PINS
        ]

        def all_off():
            for led in leds:
                led.off()

        def stop_handler(_signum, _frame):
            nonlocal running
            running = False

        signal.signal(signal.SIGINT, stop_handler)
        signal.signal(signal.SIGTERM, stop_handler)

        print("\nSTICKHANDLER PRO — 10 SENSOR EDITION")
        print("Starting self-test: LEDs will light one by one.")
        all_off()
        for led in leds:
            if not running:
                break
            led.on()
            sleep(0.15)
            led.off()

        if not running:
            return

        print("\nReady. Move the puck over the sensor matching the lit LED.")
        print(f"Round length: {ROUND_SECONDS} seconds.")
        sleep(START_DELAY_SECONDS)

        start_time = monotonic()
        while running and monotonic() - start_time < ROUND_SECONDS:
            # Choose a target different from the previous one when possible.
            choices = list(range(len(leds)))
            if target is not None and len(choices) > 1:
                choices.remove(target)
            target = choice(choices)
            all_off()
            leds[target].on()
            print(f"Target: {target + 1} | Score: {score}")

            # Wait for the correct sensor, while allowing the round to time out.
            while running and monotonic() - start_time < ROUND_SECONDS:
                now = monotonic()
                triggered = [i for i, sensor in enumerate(sensors) if sensor.is_pressed]
                if triggered and now - last_hit_time >= DEBOUNCE_SECONDS:
                    last_hit_time = now
                    if target in triggered:
                        score += 1
                        hits += 1
                        print(f" HIT! Score: {score}")
                        break
                    else:
                        print("Wrong sensor — try the lit one.")
                        # Wait for the puck/magnet to leave the sensor before continuing.
                        while running and any(s.is_pressed for s in sensors):
                            sleep(0.02)
                sleep(0.01)

        all_off()
        print("\nROUND OVER")
        print(f"Score: {score}")
        print("To play again, run: python3 stickhandler10.py")

    except Exception as exc:
        print(f"\nERROR: {exc}", file=sys.stderr)
        print("Check the GPIO pin list, wiring, and gpiozero installation.", file=sys.stderr)
        raise
    finally:
        for led in leds:
            try:
                led.off()
                led.close()
            except Exception:
                pass
        for sensor in sensors:
            try:
                sensor.close()
            except Exception:
                pass


if __name__ == "__main__":
    main()
