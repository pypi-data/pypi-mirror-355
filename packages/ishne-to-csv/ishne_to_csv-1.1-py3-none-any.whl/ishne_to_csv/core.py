import struct
import pandas as pd
import datetime
from tqdm import tqdm
import json
import os

def read_ishne(file_path_ishne , verbose=True, metadata_file=None):
    with open(file_path_ishne, 'rb') as f:
        magic = f.read(8).decode('ascii')
        if magic != 'ISHNE1.0':
            raise ValueError("Not a valid ISHNE file")

        f.read(2)  # Checksum
        variable_header_size = struct.unpack('<I', f.read(4))[0]
        total_samples = struct.unpack('<I', f.read(4))[0]
        offset_variable_header = struct.unpack('<I', f.read(4))[0]
        offset_data = struct.unpack('<I', f.read(4))[0]
        version = struct.unpack('<H', f.read(2))[0]

        first_name = f.read(40).decode('ascii').strip('\x00')
        last_name = f.read(40).decode('ascii').strip('\x00')
        subject_id = f.read(20).decode('ascii').strip('\x00')
        sex = struct.unpack('<H', f.read(2))[0]
        race = struct.unpack('<H', f.read(2))[0]

        birth_date = struct.unpack('<HHH', f.read(6))
        record_date = struct.unpack('<HHH', f.read(6))
        file_date = struct.unpack('<HHH', f.read(6))
        start_time = struct.unpack('<BBB', f.read(3))
        f.read(3)  # Reserved

        num_leads = struct.unpack('<H', f.read(2))[0]
        lead_spec = struct.unpack('<' + 'H' * 12, f.read(24))[:num_leads]
        f.read(24)  # Lead quality
        f.read(24)  # Amplitude resolution
        f.read(2)   # Pacemaker code
        f.read(40)  # Recorder type
        sampling_rate = struct.unpack('<H', f.read(2))[0]

        if sampling_rate == 0:
            raise ValueError("Invalid sampling rate read from file")


        ishne_filename = os.path.basename(file_path_ishne)

        details = {
            "Filename": ishne_filename,
            "Name": f"{first_name} {last_name}",
            "Subject ID": subject_id,
            "Sex": sex,
            "Race": race,
            "Record Date": f"{record_date[0]:02d}-{record_date[1]:02d}-{record_date[2]}",
            "Start Time": f"{start_time[0]:02d}:{start_time[1]:02d}:{start_time[2]:02d}",
            "Leads": num_leads,
            "Samples": total_samples,
            "Sampling Hz": sampling_rate,
        }

        
        if verbose:
            print("\nISHNE File Info:")
            for key, value in details.items():
                print(f"  {key:<12}: {value}")
            print()

            
        with open(metadata_file, 'w') as f_metadata:
            json.dump(details, f_metadata, indent=4)
            if verbose:
                print(f"JSON file written to: {metadata_file}")


        f.seek(offset_data)
        data = []
        iterator = tqdm(range(total_samples), disable=not verbose, desc="Reading ECG Samples")

        for _ in iterator:
            data.append([struct.unpack('<h', f.read(2))[0] for _ in range(num_leads)])

        df = pd.DataFrame(data, columns=[f'Lead_{i}' for i in range(num_leads)])

        start_datetime = datetime.datetime(
            year=record_date[2], month=record_date[1], day=record_date[0],
            hour=start_time[0], minute=start_time[1], second=start_time[2]
        )
        base_epoch_ns = int(start_datetime.timestamp() * 1e9)
        interval_ns = int(1e9 / sampling_rate)
        df.insert(0, 'time', [base_epoch_ns + i * interval_ns for i in range(total_samples)])

        return df


def ishne_to_csv(input_file, output_file=None, metadata_file=None, verbose=True):
    if not output_file:
        base, _ = os.path.splitext(input_file)
        output_file = base + '.csv'
    
    if not metadata_file:
        base, _ = os.path.splitext(input_file)
        metadata_file = base + '.json'

    df = read_ishne(input_file, metadata_file=metadata_file, verbose=verbose)
    
    if verbose:
        print(f"Writing to: {output_file}")
    
    df.to_csv(output_file, index=False)

    if verbose:
        print(f"CSV file written to: {output_file}")


