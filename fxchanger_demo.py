from fxchanger import FxChanger
from time import sleep
from numpy import arange

fxchanger = FxChanger()

# run across all available effects
def run_demo():
    for fx_id, fx in enumerate(fxchanger.fx_list):
        gradually_increase(fx_id, step=0.25, pause=2) 
        gradually_increase(fx_id, step=0.1, pause=0.5)
        wobble(fx_id, val1=0.3, val2=0.7, times=5, pause=1)
        wobble(fx_id, val1=0.1, val2=0.9, times=20, pause=0.1)


def gradually_increase(fx_id, step, pause):
    # make gradient steps from 0.0 to 1.1 with the given @step
    fx_vals = arange(0.0, 1.0, step)
    for fx_val in fx_vals:
        # play these steps with the givne @pause between them
        fxchanger.set(fx_id, fx_val)
        sleep(pause)
    fxchanger.reset(fx_id)


def wobble(fx_id, val1, val2, times, pause):
    # change the fx value to val1 and val2, back and forth many times
    for n in range(times):
        fxchanger.set(fx_id, val1)
        sleep(pause)
        fxchanger.set(fx_id, val2)
        sleep(pause)
    fxchanger.reset(fx_id)


run_demo()