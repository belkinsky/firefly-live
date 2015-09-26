import collections
import pygame
import pygame.midi as midi

pygame.init()
midi.init()

class MidiMsg:
    """The class is only a static helper for generating binary MIDI messages.
    see: http://www.midi.org/techspecs/midimessages.php"""
    
    class Commands:
        NOTE_OFF = 0x80
        NOTE_ON = 0x90
        POLYPHONIC_AFTERTOUCH = 0xA0
        CONTROL_CHANGE = 0xB0
        PROGRAM_CHANGE = 0xC0
        CHANNEL_AFTERTOUCH = 0xD0
        PITCH_BEND = 0xE0
    
    @staticmethod
    def make(channel, command, param1, param2):
        assert 0x0 <= channel <= 0xF
        assert (command & 0xF) == 0
        return (command | channel, param1, param2)
    

class MidiCcMsg:
    """The helper for generating "Control Change" messages.
    
    MidiCcMsg is a MidiMsg with:
       command = CONTROL_CHANGE
       param1  = controller_number (see Controllers below)
       param2  = cc_value (we change this value of the effect)
    """ 
    CC_CNUM_BITS = 8
    CC_CNUM_MAX = (1 << CC_CNUM_BITS) - 1
    CC_VAL_BITS = 7
    CC_VAL_MAX = (1 << CC_VAL_BITS) - 1
    
    class Controllers:
        BANK = 0x00
        MODULATION = 0x01
        BREATH = 0x02
        FOOT = 0x04
        PORTAMENTO_TIME = 0x05
        DATA_ENTRY_MSB = 0x06
        VOLUME = 0x07
        BALANCE = 0x08
        PAN = 0x0A
        EXPRESSION = 0x0B
        EFFECT1 = 0x0C
        EFFECT2 = 0x0D
        DAMPER = 0x40
        PORTAMENTO = 0x41
        SOSTENUTO = 0x42
        SOFT_PEDAL = 0x43
        LEGATO = 0x44
        HOLD2 = 0x45
    
    @staticmethod    
    def map_float_to_int(float_val):
        """
        Convert a float value (of range 0.0 to 1.0) to a MIDI integer.
        
        The float value is much more abstract and better, so we use float when
        we can, and convert it to MIDI integer only when we generate messages.
        
        At this point the mapping is linear, but probably we will need some
        non-linear (logarithmic, etc) mapping for certain controllers.
        """
        int_val = int(round(float_val * MidiCcMsg.CC_VAL_MAX, 0))
        return int_val
        
    @staticmethod
    def make(channel, controller_num, float_val):
        assert 0 <= controller_num <= MidiCcMsg.CC_CNUM_MAX
        int_val = MidiCcMsg.map_float_to_int(float_val)
        assert 0 <= int_val <= MidiCcMsg.CC_VAL_MAX
        return MidiMsg.make(channel, MidiMsg.Commands.CONTROL_CHANGE, controller_num, int_val)


class MidiCcFx():
    """An effect that implemented with MIDI Control Change messages.
    I.e. each change of the FX emits a corresponding MIDI CC message."""
    
    def __init__(self, midi_out, channel_num=0, controller_num=0, default_val=0.5):
        self.midi_out = midi_out
        self.channel_num = channel_num
        self.controller_num = controller_num
        self.default_val = default_val
    
    def set(self, fx_val):
        msg = MidiCcMsg.make(self.channel_num, self.controller_num, fx_val)
        self.midi_out.write_short(*msg)
        
    def reset(self):
        self.set(self.default_val)


class FxChanger():
    def __init__(self, device_id=0):
        self.init_midi_out(device_id)
        self.init_fx_list()
    
    def __del__(self):
        pass
        #self.clean_midi_out()
        
    def init_midi_out(self, device_id):
        print("Opening MIDI device: %s" % str(midi.get_device_info(device_id)))
        self.midi_out = midi.Output(device_id)
    
    def clean_midi_out(self):
        print("Closing MIDI device")
        self.midi_out.close()
        
    def init_fx_list(self):
        # MIDI channels/controllers are hardcoded.
        # TODO: make some GUI to adjust them.
        o = self.midi_out
        self.fx_list = [
            MidiCcFx(o, channel_num=7, controller_num=0),
            MidiCcFx(o, channel_num=10, controller_num=1),
        ]
    
    def set(self, fx_id, fx_val):
        """Set the (absolute) value of an effect (from 0.0 to 1.0)."""
        assert 0.00 <= fx_val <= 1.00
        fx = self.fx_list[fx_id]
        fx.set(fx_val)
    
    def reset(self, fx_id):
        """Reset an effect to its default value."""
        fx = self.fx_list[fx_id]
        fx.reset()
