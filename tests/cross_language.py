import subprocess
import os
import sys

# Ensure we import the local module
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../python')))
from edlora import Packet, MsgType

def run_cpp_exporter():
    cpp_source = "cpp_exporter.cpp"
    cpp_obj = "../cpp/edlora.cpp"
    executable = "./cpp_exporter"
    
    # Compile
    print("Compiling C++ exporter...")
    compile_cmd = ["g++", cpp_source, cpp_obj, "-o", executable, "-std=c++11", "-I../cpp"]
    subprocess.run(compile_cmd, check=True)
    
    # Run
    print("Running C++ exporter...")
    result = subprocess.run([executable], capture_output=True, text=True, check=True)
    
    test_outputs = {}
    for line in result.stdout.strip().split('\n'):
        if line.startswith("TEST"):
            key, val = line.split(":")
            test_outputs[key] = val
            
    return test_outputs

def main():
    cpp_results = run_cpp_exporter()
    
    # Generate same tests in Python
    # Test 1
    p1 = Packet(sender_id=42, receiver_id=100, msg_type=MsgType.HEARTBEAT, seq_num=1, timestamp=0x11223344)
    py_test1 = p1.pack().hex()
    
    # Test 2
    p2 = Packet(sender_id=255, receiver_id=0, msg_type=MsgType.CUSTOM, seq_num=200, timestamp=0xFFEEDDCC)
    p2.set_payload_string("TEKNOFEST2026")
    py_test2 = p2.pack().hex()
    
    # Test 3
    p3_payload = bytes(i & 0xFF for i in range(240))
    p3 = Packet(sender_id=1, receiver_id=2, msg_type=MsgType.SYS_STATE, seq_num=255, timestamp=99999999, payload=p3_payload)
    py_test3 = p3.pack().hex()
    
    errors = 0
    print("\n--- Cross-Language Verification ---")
    
    def check(name, py_hex, cpp_hex):
        nonlocal errors
        match_str = "MATCH" if py_hex == cpp_hex else "FAIL"
        print(f"[{name}] {match_str}")
        if py_hex != cpp_hex:
            print(f"  Python: {py_hex}")
            print(f"  C++   : {cpp_hex}")
            errors += 1
            
    check("TEST1 (Heartbeat)", py_test1, cpp_results["TEST1"])
    check("TEST2 (String Payload)", py_test2, cpp_results["TEST2"])
    check("TEST3 (Max Bin Payload)", py_test3, cpp_results["TEST3"])
    
    # Verify unpacking consistency as well:
    # Let Python unpack what C++ made!
    print("\n[Unpack Verification]")
    try:
        up1 = Packet.unpack(bytes.fromhex(cpp_results["TEST1"]))
        assert up1.sender_id == 42
        assert up1.timestamp == 0x11223344
        assert up1.payload_len == 0
        print("TEST1 Unpack: MATCH")
    except Exception as e:
        print(f"TEST1 Unpack: FAIL ({e})")
        errors += 1
        
    try:
        up2 = Packet.unpack(bytes.fromhex(cpp_results["TEST2"]))
        assert up2.get_payload_string() == "TEKNOFEST2026"
        print("TEST2 Unpack: MATCH")
    except Exception as e:
        print(f"TEST2 Unpack: FAIL ({e})")
        errors += 1

    if errors == 0:
        print("\nAll byte-for-byte cross-language tests PASSED!")
        sys.exit(0)
    else:
        print(f"\n{errors} error(s) detected. Protocol models mismatch!")
        sys.exit(1)

if __name__ == "__main__":
    main()
