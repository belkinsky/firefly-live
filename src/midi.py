import atexit
import ctypes.util

lib_name = ctypes.util.find_library('portmidi')
libportmidi = ctypes.cdll.LoadLibrary(lib_name)

# typedef enum {...} PmError;
PmError = ctypes.c_int

# const char *Pm_GetErrorText( PmError errnum )
Pm_GetErrorText = libportmidi.Pm_GetErrorText
Pm_GetErrorText.restype = ctypes.c_char_p
Pm_GetErrorText.argtypes = (PmError,)

def _check_PmError(err_code, *unused_args):
    if err_code:
        raise Exception(Pm_GetErrorText(err_code))

def _import(fn_name, restype, *argtypes): 
    fn = getattr(libportmidi, fn_name)
    fn.restype = restype
    fn.argtypes = argtypes
    if restype == PmError:
        fn.errcheck = _check_PmError
    return fn
    
# PmError Pm_Initialize( void );
Pm_Initialize = _import('Pm_Initialize', PmError)

# PmError Pm_Terminate( void );
Pm_Terminate = _import('Pm_Terminate', PmError)

# PmError Pm_OpenOutput(
#     PortMidiStream** stream, PmDeviceID outputDevice,  void *outputDriverInfo, 
#     int32_t bufferSize,      PmTimeProcPtr time_proc,  void *time_info,
#     int32_t latency
# );
Pm_OpenOutput = _import('Pm_OpenOutput', PmError,
                        ctypes.c_void_p, ctypes.c_int32, ctypes.c_void_p,
                        ctypes.c_int32, ctypes.c_void_p, ctypes.c_void_p,
                        ctypes.c_int32) 

# PmError Pm_Close( PortMidiStream* stream );
Pm_Close = _import('Pm_Close', PmError, ctypes.c_void_p)

# PmError Pm_WriteShort( PortMidiStream *stream, PmTimestamp when, int32_t msg);
Pm_WriteShort = _import('Pm_WriteShort', PmError, ctypes.c_void_p, ctypes.c_int32, ctypes.c_int32)


# 
Pm_Initialize()
atexit.register(Pm_Terminate)


class Output():
    """
    The interface class for the portmidi PmStream (the output one) and
    related functions: Pm_OpenOutput/Pm_WriteShort/Pm_Close.
    
    Usage:
    with Output(device_id) as o:
        o.write(Msg.make(0, Msg.Commands.NOTE_ON, 60, 127))
        o.write(Msg.make(0, Msg.Commands.NOTE_ON, 63, 127))
        o.write(Msg.make(0, Msg.Commands.NOTE_ON, 67, 127))
        sleep(1)
        o.write(CcMsg.make(0, CcMsg.ChannelMode.ALL_NOTES_OFF, 0))
    """
    def __init__(self, dev_id=0):
        self.dev_id = dev_id
    
    def __enter__(self):
        self.open()
        return self
        
    def __exit__(self, *unused_args):
        self.close()
        
    def __del__(self):
        if (self.is_open()):
            self.close()
    
    def open(self):
        # The libportmidi allocates a PortMidiStream strcuture and sets our pointer
        # to this strucutre. We pass a reference to this pointer as an argument. 
        stream_p  = ctypes.c_void_p(None)   # "struct PortMidiStream *"
        stream_pp = ctypes.byref(stream_p)  # "struct PortMidiStream **"
        
        dev_id    = ctypes.c_int32(self.dev_id)
        
        # No buffering at all.
        drv_info  = ctypes.c_void_p(None)
        buf_size  = ctypes.c_int32(0)
        time_proc = ctypes.c_void_p(None)
        time_info = ctypes.c_void_p(None)
        latency   = ctypes.c_int32(0)
        
        Pm_OpenOutput(stream_pp, dev_id, drv_info, buf_size, time_proc, time_info, latency)
        self.stream_p = stream_p
    
    def is_open(self):
        return hasattr(self, 'stream_p')
    
    def close(self):
        Pm_Close(self.stream_p)
        del self.stream_p
    
    def write(self, msg_3_bytes_tuple):
        status, data1, data2 = msg_3_bytes_tuple
        assert 0 <= status <= 0xFF
        assert 0 <= data1 <= 0xFF
        assert 0 <= data2 <= 0xFF
        data1 <<= 8
        data2 <<= 16
        
        midi_msg = ctypes.c_int32(status | data1 | data2)
        timestamp = ctypes.c_int32(0)
        
        print("send midi message: %s" % str(msg_3_bytes_tuple))
        Pm_WriteShort(self.stream_p, timestamp, midi_msg)


class Msg:
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


class CcMsg:
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
        assert 0 <= controller_num <= CcMsg.CC_CNUM_MAX
        assert 0 <= int_val <= CcMsg.CC_VAL_MAX
        return Msg.make(channel, Msg.Commands.CONTROL_CHANGE, controller_num, int_val)
    

# Play a tiny demo when the file is executed.
if __name__ == '__main__':
    from time import sleep
    device_id = 2
    with Output(device_id) as o:
        o.write(Msg.make(0, Msg.Commands.NOTE_ON, 65, 127))
        o.write(Msg.make(0, Msg.Commands.NOTE_ON, 69, 127))
        o.write(Msg.make(0, Msg.Commands.NOTE_ON, 72, 127))
        sleep(1)
        o.write(CcMsg.make(0, CcMsg.ChannelMode.ALL_NOTES_OFF, 0))
        o.write(Msg.make(0, Msg.Commands.NOTE_ON, 60, 127))
        o.write(Msg.make(0, Msg.Commands.NOTE_ON, 63, 127))
        o.write(Msg.make(0, Msg.Commands.NOTE_ON, 67, 127))
        sleep(1)

        o.write(CcMsg.make(0, CcMsg.ChannelMode.ALL_NOTES_OFF, 0))