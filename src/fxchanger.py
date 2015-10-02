import collections
import midi
from midi.output import MidiOutput
from midi.msg import MidiMsg, MidiCcMsg

class MidiCcFx():
    """An effect that implemented with MIDI Control Change messages.
    I.e. each change of the FX emits a corresponding MIDI CC message."""
    
    @staticmethod    
    def map_float_to_int(float_val):
        """
        Convert a float value (of range 0.0 to 1.0) to a MIDI integer.
        
        The float value is much more abstract and better, so we use float when
        we can, and convert it to MIDI integer only when we generate messages.
        
        At this point the mapping is linear, but probably we will need some
        non-linear (logarithmic, etc) mapping for certain controllers.
        """
        assert 0.00 <= float_val <= 1.00
        int_val = int(round(float_val * MidiCcMsg.CC_VAL_MAX, 0))
        return int_val
    
    def __init__(self, midi_out, channel_num=0, controller_num=0, default_val=0.5):
        self.midi_out = midi_out
        self.channel_num = channel_num
        self.controller_num = controller_num
        self.default_val = default_val
    
    def set(self, fx_val):
        int_val = MidiCcFx.map_float_to_int(fx_val)
        msg = MidiCcMsg.make(self.channel_num, self.controller_num, int_val)
        self.midi_out.write(msg)
        
    def reset(self):
        self.set(self.default_val)


class FxChanger():
    def __init__(self, device_id=0):
        self.init_midi_out(device_id)
        self.init_fx_list()
        
    def init_midi_out(self, device_id):
        self.midi_out = MidiOutput(device_id)
        self.midi_out.open()

    class FX_ID:
        A = 0
        B = 1
        C = 2

    def init_fx_list(self):
        # MIDI channels/controllers are hardcoded.
        # TODO: make some GUI to adjust them.
        o = self.midi_out
        self.fx_list = [
            MidiCcFx(o, channel_num=7, controller_num=0),
            MidiCcFx(o, channel_num=10, controller_num=1),
            MidiCcFx(o, channel_num=14, controller_num=42), #TODO: set actual channel and controller
        ]
    
    def set(self, fx_id, fx_val):
        """Set the (absolute) value of an effect (from 0.0 to 1.0)."""
        fx = self.fx_list[fx_id]
        fx.set(fx_val)
    
    def reset(self, fx_id):
        """Reset an effect to its default value."""
        fx = self.fx_list[fx_id]
        fx.reset()
