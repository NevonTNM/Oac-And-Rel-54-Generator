import re

# Events and parameters
event_hashes = {
    "track_id": 0xA6D93246,
    "intro_start": 0x08DBA0F8,
    "intro_end": 0x08DBA0F8,
    "outro_start": 0x08DBA0F8,
    "outro_end": 0x08DBA0F8,
    "beat": 0xE89AE78C,
    "rock_in": 0xF31B4F6A,
    "rock_out": 0xF31B4F6A,
}

param_hashes = {
    "track_id": 0x45807800,  # BUGGED, USER SETS TRACKID HIMSELF
    "intro_start": 0x449687BA,
    "intro_end": 0x2CC6E05E,
    "outro_start": 0x7DCE9FA0,
    "outro_end": 0x71D8DCAD,
    "beat": 0x41800000,
    "rock_in": 0x84DC271F,
    "rock_out": 0xB0C485D7,
}

# Parsing input
def parse_input(input_file):
    with open(input_file, 'r') as f:
        lines = f.readlines()

    parsed_data = {}
    for line in lines:
        if '=' in line:
            key, value = line.strip().split(' = ')
            parsed_data[key.strip()] = value.strip()
    return parsed_data

# Parsing from Audacity
def parse_audacity_labels(audacity_timecodes):
    with open(audacity_timecodes, 'r') as f:
        lines = f.readlines()

    audacity_events = []
    for line in lines:
        start, end, label = line.strip().split('\t')

        # Converting to int and multiplying for 48 KHz
        start_timestamp = int(round(float(start) * 48000))
        
        if label == "intro":
            # Two timecodes for intro
            end_timestamp = int(round(float(end) * 48000))
            audacity_events.append((start_timestamp, "intro_start"))
            audacity_events.append((end_timestamp, "intro_end"))
        elif label == "outro":
            # Same for outro
            end_timestamp = int(round(float(end) * 48000))
            audacity_events.append((start_timestamp, "outro_start"))
            audacity_events.append((end_timestamp, "outro_end"))
        elif label == "beat":
            # Only one timestamp for beat
            audacity_events.append((start_timestamp, "beat"))

    return audacity_events

def create_oac(parsed_data, audacity_events):
    folder_name = parsed_data['folder_name']
    left_channel = parsed_data['left_channel']
    right_channel = parsed_data['right_channel']
    headroom = parsed_data.get('headroom', 121)

    # TRACKID FIXING TRYOUTS, CURRENTLY NO USAGE
    track_id = parsed_data['track_id'].upper()

    # Creating events list
    events = []

    # TrackID always first with timestamp of 0
    events.append({
        "event_hash": event_hashes["track_id"],
        "param_hash": param_hashes["track_id"],
        "timestamp": 0
    })

    # Adding events from Audacity
    for timestamp, event_name in audacity_events:
        if event_name in event_hashes:
            events.append({
                "event_hash": event_hashes[event_name],
                "param_hash": param_hashes[event_name],
                "timestamp": timestamp
            })

    # Sorting events by timestamps
    events = sorted(events, key=lambda x: x["timestamp"])

    # Oac original data
    oac_content = f"Version 1 11\n{{\n\tIsStream True\n\tStream\n\t{{\n\t\tChannel {left_channel}\n\t\t{{\n\t\t\tHeadroom {headroom}\n\t\t\tWave {folder_name}\\{left_channel}.wav\n\t\t\tEvents\n\t\t\t{{\n"

    for event in events:
        oac_content += f"\t\t\t\tEvent\n\t\t\t\t{{\n\t\t\t\t\tEventTypeHash {hex(event['event_hash']).upper()}\n\t\t\t\t\tParameterHash {hex(event['param_hash']).upper()}\n\t\t\t\t\tTimestamp {event['timestamp']}\n\t\t\t\t\tFlags 0x00000000\n\t\t\t\t}}\n"

    oac_content += f"\t\t\t}}\n\t\t}}\n\t\tChannel {right_channel}\n\t\t{{\n\t\t\tHeadroom {headroom}\n\t\t\tWave {folder_name}\\{right_channel}.wav\n\t\t\tEvents null\n\t\t}}\n\t}}\n}}\n"

    return oac_content

# SOUNDS REL 54
def create_rel(parsed_data):
    radio_name = parsed_data['radio_name']
    song_name = parsed_data['song_name']
    duration = parsed_data['duration']

    rel_content = f'''
<Item type="SimpleSound">
   <Name>{radio_name}_{song_name}_left</Name>
   <Header>
    <Flags value="0x00800040" />
    <Pan value="307" />
    <SpeakerMask value="0" />
   </Header>
   <ContainerName>{radio_name}/{song_name}</ContainerName>
   <FileName>{song_name}_left</FileName>
   <WaveSlotIndex value="0" />
  </Item>
  <Item type="SimpleSound">
   <Name>{radio_name}_{song_name}_right</Name>
   <Header>
    <Flags value="0x00800040" />
    <Pan value="53" />
    <SpeakerMask value="0" />
   </Header>
   <ContainerName>{radio_name}/{song_name}</ContainerName>
   <FileName>{song_name}_right</FileName>
   <WaveSlotIndex value="0" />
  </Item>
  <Item type="StreamingSound">
   <Name>{radio_name}_{song_name}</Name>
   <Header>
    <Flags value="0x0180C001" />
    <Flags2 value="0xAA90AAAA" />
    <DopplerFactor value="0" />
    <Category>radio_front_end</Category>
    <SpeakerMask value="0" />
    <EffectRoute value="1" />
   </Header>
   <Duration value="{duration}" />
   <ChildSounds>
    <Item>{radio_name}_{song_name}_left</Item>
    <Item>{radio_name}_{song_name}_right</Item>
   </ChildSounds>
  </Item>
  '''
    return rel_content

# Writing function
def write_oac_file(input_file, audacity_timecodes):
    parsed_data = parse_input(input_file)
    audacity_events = parse_audacity_labels(audacity_timecodes)
    oac_content = create_oac(parsed_data, audacity_events)
    rel_content = create_rel(parsed_data)
    output_file_rel = f"sounds54_rel.xml"

    # .oac writing
    output_file = f"{parsed_data['folder_name']}.oac"
    with open(output_file, 'w') as f:
        f.write(oac_content)
    # .rel writing
    with open(output_file_rel, 'w') as f:
        f.write(rel_content)

# Calling function
input_file = 'input.txt'
audacity_timecodes = 'input_timecodes.txt'
write_oac_file(input_file, audacity_timecodes)
