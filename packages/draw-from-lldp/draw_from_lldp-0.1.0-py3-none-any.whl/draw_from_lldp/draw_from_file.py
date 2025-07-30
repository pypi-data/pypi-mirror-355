from N2G import drawio_diagram
import logging
import re
from ttp import ttp


device_list = []
connections_list = []
duplicate_device_list = []

# logger
logger = logging.getLogger('logger:')
logger.setLevel(logging.INFO)
file_handler = logging.FileHandler('log/connection.log', 'a', encoding = "UTF-8")
log_format = logging.Formatter('%(asctime)s � %(name)s � %(levelname)s � %(message)s', datefmt='%D-%H:%M:%S')
file_handler.setFormatter(log_format)
logger.addHandler(file_handler)


def read_file(path_to_file):
    parser = ttp(data=path_to_file, template="./ttp/lldp.ttp")
    parser.parse()
    result = parser.result()[0][0]

    identity = set_id("asw-01")
    main_device = {
        'id': identity,
        'label': "asw-01",
        'style': "./l3_switch"
    }
    device_list.append(main_device)
    for connect in result:
        node_type = set_style(connect.get('destinationNodeID'))
        if 'Interface ' in connect.get('id_type') and node_type != '':
            identity = set_id(connect.get('destinationNodeID'))
            attribute = set_attr(connect.get('destinationLabel'), identity)
            connection = {
                'source': "asw-01",
                'target': connect.get('destinationNodeID'),
                'src_label': connect.get('sourceLabel'),
                'trgt_label': connect.get('destinationLabel'),
                'style': attribute
            }

            device = {
                'id': identity,
                'style': node_type,
                'label': connect.get('destinationNodeID')
            }
            if device['id'] not in duplicate_device_list:
                duplicate_device_list.append(device['id'])
                device_list.append(device)
            connections_list.append(connection)


def set_style(name: str):
    role = ''
    if name:
        if 'asw-01' in name:
            role = './l3_switch'
        elif 'dsw' in name:
            role = './l2_switch'
        elif 'csw' in name:
            role = './l3_switch'
        elif 'usg' in name:
            role = './firewall'
        elif 'rt' in name:
            role = './router.txt'
        elif 'asw-' in name and 'asw-01' not in name:
            role = './l2_switch'
    return role


def set_id(sysname):
    ident = re.findall(r'\w+-\d+', sysname)
    if ident != []:
        return ident[0]
    else:
        return None


def set_attr(end_point, dev_id):
    compare_part = 'endArrow=none;'
    edge = ''
    if end_point == 'MEth0/0/0':
        edge = 'edgeStyle=orthogonalEdgeStyle;rounded=0;'
        if '01' in dev_id:
            entry_point = 'entryX=0;entryDx=0;entryY=0.5;entryDy=0;'
            exit_point = 'exitX=0;exitY=0.25;exitDx=0;exitDy=0;'
        else:
            entry_point = 'entryX=1;entryDx=0;entryY=0.5;entryDy=0;'
            exit_point = 'exitX=1;exitY=0.25;exitDx=0;exitDy=0;'

    elif end_point == 'GigabitEthernet0/0/0' and 'rt-' in dev_id:
        edge = 'edgeStyle=orthogonalEdgeStyle;rounded=0;'
        if '01' in dev_id:
            entry_point = 'entryX=0;entryDx=0;entryY=0.5;entryDy=0;'
            exit_point = 'exitX=0;exitY=0.5;exitDx=0;exitDy=0;'
        else:
            entry_point = 'entryX=1;entryDx=0;entryY=0.5;entryDy=0;'
            exit_point = 'exitX=1;exitY=0.5;exitDx=0;exitDy=0;'

    elif '0/0/1' in end_point:
        if 'usg' in dev_id:
            entry_point = 'entryX=0.75;entryDx=0;entryY=1;entryDy=0;'
            exit_point = 'exitX=0.5;exitY=0;exitDx=0;exitDy=0;'
        elif 'rt' in dev_id:
            entry_point = 'entryX=0.75;entryDx=0;entryY=0;entryDy=0;'
            exit_point = 'exitX=0.5;exitY=1;exitDx=0;exitDy=0;'

    elif '0/0/2' in end_point or ('0/0/0' in end_point and 'usg' in dev_id):
        if 'usg' in dev_id:
            entry_point = 'entryX=0.5;entryDx=0;entryY=1;entryDy=0;'
            exit_point = 'exitX=0.5;exitY=0;exitDx=0;exitDy=0;'
        elif 'rt' in dev_id:
            entry_point = 'entryX=0.5;entryDx=0;entryY=0;entryDy=0;'
            exit_point = 'exitX=0.5;exitY=1;exitDx=0;exitDy=0;'

    elif '0/0/8' in end_point :
        edge = 'edgeStyle=orthogonalEdgeStyle;rounded=0;'
        if '01' in dev_id:
            entry_point = 'entryX=0;entryDx=0;entryY=0.25;entryDy=0;'
            exit_point = 'exitX=0;exitY=0.75;exitDx=0;exitDy=0;'
        elif '02' in dev_id:
            entry_point = 'entryX=1;entryDx=0;entryY=0.25;entryDy=0;'
            exit_point = 'exitX=1;exitY=0.75;exitDx=0;exitDy=0;'

    elif '0/0/9' in end_point:
        edge = 'dashed=1;'
        if '01' in dev_id:
            entry_point = 'entryX=0;entryDx=0;entryY=0;entryDy=0;'
            exit_point = 'exitX=0;exitY=0.75;exitDx=0;exitDy=0;'
        elif '02' in dev_id:
            entry_point = 'entryX=1;entryDx=0;entryY=0;entryDy=0;'
            exit_point = 'exitX=1;exitY=0.75;exitDx=0;exitDy=0;'
    else:
        entry_point = ''
        exit_point = 'exitX=0.5;exitY=1;exitDx=0;exitDy=0;'
    new_style = compare_part + entry_point + exit_point + edge
    return new_style


if __name__ == "__main__":
    logger.info("Start script...")
    read_file("./input/lldp.txt")
    logger.info("Process diagram...")
    sample_graph = {
        "node": device_list,
        "links": connections_list
    }
    new_ip = "asw-01"
    diagram = drawio_diagram()
    diagram.from_dict(sample_graph, width=1000, height=800, diagram_name=f"{new_ip}")
    diagram.layout(algo="circle")
    logger.info("Drop diagram...")
    diagram.dump_file(filename=f"{new_ip}.drawio", folder="./output/")
    logger.info("The task completes")
