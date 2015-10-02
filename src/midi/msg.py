
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

    class ChannelMode:
        ALL_NOTES_OFF = 0x7B

    @staticmethod
    def make(channel, controller_num, int_val):
        assert 0 <= controller_num <= MidiCcMsg.CC_CNUM_MAX
        assert 0 <= int_val <= MidiCcMsg.CC_VAL_MAX
        return MidiMsg.make(channel,
                            MidiMsg.Commands.CONTROL_CHANGE,
                            controller_num,
                            int_val)
