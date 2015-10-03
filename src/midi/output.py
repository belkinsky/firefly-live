import atexit
import ctypes.util
from ctypes import c_int, c_int32, c_char_p, c_void_p, POINTER, Structure
from ctypes import cast, byref

lib_name = ctypes.util.find_library('portmidi')
libportmidi = ctypes.cdll.LoadLibrary(lib_name)


# =============================================================================
#  typedefs
# =============================================================================

def _typedef(base_class, new_class_name):
    """A shortcut for defining new classes with a single line of code."""
    return type(new_class_name, (base_class,), {})

# typedef enum {...} PmError;
PmError = _typedef(c_int, 'PmError')

# typedef int PmDeviceID;
PmDeviceID = _typedef(c_int, 'PmDeviceID')

# typedef void PmStream;
# Note: we can't actually define "void", so we define a pointer to it.
PmStreamPtr = _typedef(c_void_p, 'PmStreamPtr')

# typedef int32_t PmTimestamp;
PmTimestamp = _typedef(c_int32, 'PmTimestamp')

# typedef PmTimestamp (*PmTimeProcPtr)(void *time_info);
PmTimeProcPtr = ctypes.CFUNCTYPE(PmTimestamp, c_void_p)


# typedef struct {
#     int structVersion; /**< this internal structure version */
#     const char *interf; /**< underlying MIDI API, e.g. MMSystem or DirectX */
#     const char *name;   /**< device name, e.g. USB MidiSport 1x1 */
#     int input; /**< true iff input is available */
#     int output; /**< true iff output is available */
#     int opened; /**< used by generic PortMidi code to do error checking on arguments */
# } PmDeviceInfo;
class PmDeviceInfo(Structure):
    _fields_ = [('structVersion', c_int),
                ('interf', c_char_p),
                ('name', c_char_p),
                ('input', c_int),
                ('output', c_int),
                ('opened', c_int)]

# A shortcut for "PmDeviceInfo *" (because in C you never pass it by value).
PmDeviceInfoPtr = POINTER(PmDeviceInfo)


# =============================================================================
#  function imports
# =============================================================================

class MidiPmError(Exception):
    pass

# const char *Pm_GetErrorText( PmError errnum )
Pm_GetErrorText = libportmidi.Pm_GetErrorText
Pm_GetErrorText.restype = c_char_p
Pm_GetErrorText.argtypes = (PmError,)

def _check_PmError(err_code, *unused_args):
    if err_code:
        raise MidiPmError(Pm_GetErrorText(err_code))


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

# int Pm_CountDevices( void );
Pm_CountDevices = _import('Pm_CountDevices', c_int)

# PmDeviceID Pm_GetDefaultInputDeviceID( void );
Pm_GetDefaultOutputDeviceID = _import('Pm_GetDefaultOutputDeviceID', PmDeviceID)

# const PmDeviceInfo* Pm_GetDeviceInfo( PmDeviceID id );
Pm_GetDeviceInfo = _import('Pm_GetDeviceInfo', PmDeviceInfoPtr, PmDeviceID)

# PmError Pm_OpenOutput(
#     PortMidiStream** stream, PmDeviceID outputDevice, void *outputDriverInfo,
#     int32_t bufferSize,      PmTimeProcPtr time_proc, void *time_info,
#     int32_t latency
# );
Pm_OpenOutput = _import('Pm_OpenOutput', PmError,
                        POINTER(PmStreamPtr), PmDeviceID, c_void_p,
                        c_int32, PmTimeProcPtr, c_void_p,
                        c_int32)

# PmError Pm_Close( PortMidiStream* stream );
Pm_Close = _import('Pm_Close', PmError, PmStreamPtr)

# PmError Pm_WriteShort(PortMidiStream *stream, PmTimestamp when, int32_t msg);
Pm_WriteShort = _import('Pm_WriteShort', PmError,
                        PmStreamPtr, PmTimestamp, c_int32)


# =============================================================================
#  MidiOutput implementation
# =============================================================================

# TODO: check that all outputs are closed at the time Pm_Terminate is called
Pm_Initialize()
atexit.register(Pm_Terminate)


class MidiNoOutputException(Exception):
    pass


class MidiOutput():
    """The interface class for the portmidi's PmStream (the output one)
    and various related functions: Pm_OpenOutput/Pm_WriteShort/Pm_Close/etc.

    Usage:
    with MidiOutput() as o:
        o.write((0x90, 60, 127))  # NoteOn
        o.write((0x90, 64, 127))
        o.write((0x90, 67, 127))
        sleep(1)
        o.write((0xB0, 0x7B, 0))  # AllNotesOff
    """

    def __init__(self, device_id=None):
        if device_id is None:
            device_id = Pm_GetDefaultOutputDeviceID().value
        self.device_id = device_id

        device_info = Pm_GetDeviceInfo(device_id).contents
        self.device_name = device_info.name
        self.interface_name = device_info.interf

        if not device_info.output:
            msg = "Can't create MidiOutput() on a non-output device: %s" % self
            raise MidiNoOutputException(msg)

    def __enter__(self):
        self.open()
        return self

    def __exit__(self, *unused_args):
        self.close()

    def __del__(self):
        if (self.is_open()):
            self.close()

    def __str__(self):
        return ("MIDI Output #%d: %s - %s" %
                (self.device_id, self.interface_name, self.device_name))

    def __repr__(self):
        return ("%s(%d, '%s', '%s')" % (self.__class__,
                self.device_id, self.device_name, self.interface_name))

    def open(self):
        # The libportmidi allocates a PortMidiStream strcuture and sets our
        # pointer to this strucutre. We pass a reference to this pointer as an
        # argument.
        stream_ptr = PmStreamPtr()
        device_id = PmDeviceID(self.device_id)

        # No buffering/timing at all.
        drv_info = c_void_p(None)
        buf_size = c_int32(0)
        time_proc = cast(None, PmTimeProcPtr)
        time_info = c_void_p(None)
        latency = c_int32(0)

        Pm_OpenOutput(byref(stream_ptr), device_id,
                      drv_info, buf_size, time_proc, time_info, latency)
        self.stream_ptr = stream_ptr

    def is_open(self):
        return hasattr(self, 'stream_ptr')

    def close(self):
        Pm_Close(self.stream_ptr)
        del self.stream_ptr

    def write(self, msg_3_bytes_tuple):
        status, data1, data2 = msg_3_bytes_tuple
        assert 0 <= status <= 0xFF
        assert 0 <= data1 <= 0xFF
        assert 0 <= data2 <= 0xFF
        data1 <<= 8
        data2 <<= 16

        midi_msg = c_int32(status | data1 | data2)
        timestamp = PmTimestamp(0)

        print("send midi message: %s" % str(msg_3_bytes_tuple))
        Pm_WriteShort(self.stream_ptr, timestamp, midi_msg)

    @staticmethod
    def discover():
        """Get a list of all available MIDI outputs (as MidiOutput objects)."""
        found_outputs = []
        device_count = Pm_CountDevices()
        for device_id in range(device_count):
            try:
                found_outputs.append(MidiOutput(device_id))
            except MidiNoOutputException:
                pass
        return found_outputs


# =============================================================================
#  test/demo
# =============================================================================
# When the file is executed, try to discover all available MIDI outputs,
# and play a short demo (a couple of notes and a chord) to each output.

if __name__ == '__main__':
    from time import sleep
    for output in MidiOutput.discover():
        print('playing few notes to: %s' % output)
        with output as o:
            sleep(1)
            o.write((0x90, 65, 127))  # 0x90 - Note ON
            sleep(0.3)
            o.write((0x90, 70, 127))
            sleep(0.3)
            o.write((0x90, 72, 127))
            sleep(0.3)
            o.write((0xB0, 0x7B, 0))  # 0xB0 - All Notes OFF
            o.write((0x90, 60, 127))
            o.write((0x90, 64, 127))
            o.write((0x90, 67, 127))
            sleep(1)
            o.write((0xB0, 0x7B, 0))
