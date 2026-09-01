demo_graph = {
    "module": "flowpipe.graph",
    "cls": "Graph",
    "name": "World Clock",
    "nodes": [
        {
            "file_location": "C:\\Users\\Simon Weck\\Desktop\\Bachelor\\VEXS-Backend\\src\\services\\flowpipe_service.py",
            "module": "flowpipe.node",
            "cls": "FunctionNode",
            "name": "CurrentTime",
            "identifier": "CurrentTime-bfb3c2a4-15c6-43e0-992f-018f8e18a3ef",
            "inputs": {},
            "outputs": {
                "time": {
                    "name": "time",
                    "value": None,
                    "connections": {
                        "Vancouver-4af536a8-5708-4c8c-b7f0-2e3f228806ae": ["time"],
                        "London-20b83732-8390-4180-8b9f-35962a7163f8": ["time"],
                        "Munich-acf91c42-1d42-4047-882f-6932d7f256ae": ["time"],
                    },
                    "sub_plugs": {},
                }
            },
            "metadata": {},
            "func": {"module": "src.services.flowpipe_service", "name": "CurrentTime"},
        },
        {
            "file_location": "C:\\Users\\Simon Weck\\Desktop\\Bachelor\\VEXS-Backend\\src\\services\\flowpipe_service.py",
            "module": "src.services.flowpipe_service",
            "cls": "ConvertTime",
            "name": "Vancouver",
            "identifier": "Vancouver-4af536a8-5708-4c8c-b7f0-2e3f228806ae",
            "inputs": {
                "time": {
                    "name": "time",
                    "value": None,
                    "connections": {"CurrentTime-bfb3c2a4-15c6-43e0-992f-018f8e18a3ef": "time"},
                    "sub_plugs": {},
                },
                "timezone": {
                    "name": "timezone",
                    "value": -8,
                    "connections": {},
                    "sub_plugs": {},
                },
            },
            "outputs": {
                "converted_time": {
                    "name": "converted_time",
                    "value": None,
                    "connections": {
                        "ShowTimes-d64ee37b-620b-4318-95b7-e695e32e6b9f": ["times.Vancouver"]
                    },
                    "sub_plugs": {},
                }
            },
            "metadata": {},
        },
        {
            "file_location": "C:\\Users\\Simon Weck\\Desktop\\Bachelor\\VEXS-Backend\\src\\services\\flowpipe_service.py",
            "module": "src.services.flowpipe_service",
            "cls": "ConvertTime",
            "name": "London",
            "identifier": "London-20b83732-8390-4180-8b9f-35962a7163f8",
            "inputs": {
                "time": {
                    "name": "time",
                    "value": None,
                    "connections": {"CurrentTime-bfb3c2a4-15c6-43e0-992f-018f8e18a3ef": "time"},
                    "sub_plugs": {},
                },
                "timezone": {
                    "name": "timezone",
                    "value": 0,
                    "connections": {},
                    "sub_plugs": {},
                },
            },
            "outputs": {
                "converted_time": {
                    "name": "converted_time",
                    "value": None,
                    "connections": {
                        "ShowTimes-d64ee37b-620b-4318-95b7-e695e32e6b9f": ["times.London"]
                    },
                    "sub_plugs": {},
                }
            },
            "metadata": {},
        },
        {
            "file_location": "C:\\Users\\Simon Weck\\Desktop\\Bachelor\\VEXS-Backend\\src\\services\\flowpipe_service.py",
            "module": "src.services.flowpipe_service",
            "cls": "ConvertTime",
            "name": "Munich",
            "identifier": "Munich-acf91c42-1d42-4047-882f-6932d7f256ae",
            "inputs": {
                "time": {
                    "name": "time",
                    "value": None,
                    "connections": {"CurrentTime-bfb3c2a4-15c6-43e0-992f-018f8e18a3ef": "time"},
                    "sub_plugs": {},
                },
                "timezone": {
                    "name": "timezone",
                    "value": 1,
                    "connections": {},
                    "sub_plugs": {},
                },
            },
            "outputs": {
                "converted_time": {
                    "name": "converted_time",
                    "value": None,
                    "connections": {
                        "ShowTimes-d64ee37b-620b-4318-95b7-e695e32e6b9f": ["times.Munich"]
                    },
                    "sub_plugs": {},
                }
            },
            "metadata": {},
        },
        {
            "file_location": "C:\\Users\\Simon Weck\\Desktop\\Bachelor\\VEXS-Backend\\src\\services\\flowpipe_service.py",
            "module": "flowpipe.node",
            "cls": "FunctionNode",
            "name": "ShowTimes",
            "identifier": "ShowTimes-d64ee37b-620b-4318-95b7-e695e32e6b9f",
            "inputs": {
                "times": {
                    "name": "times",
                    "value": None,
                    "connections": {},
                    "sub_plugs": {
                        "Vancouver": {
                            "name": "times.Vancouver",
                            "value": None,
                            "connections": {
                                "Vancouver-4af536a8-5708-4c8c-b7f0-2e3f228806ae": "converted_time"
                            },
                        },
                        "London": {
                            "name": "times.London",
                            "value": None,
                            "connections": {
                                "London-20b83732-8390-4180-8b9f-35962a7163f8": "converted_time"
                            },
                        },
                        "Munich": {
                            "name": "times.Munich",
                            "value": None,
                            "connections": {
                                "Munich-acf91c42-1d42-4047-882f-6932d7f256ae": "converted_time"
                            },
                        },
                    },
                }
            },
            "outputs": {},
            "metadata": {},
            "func": {"module": "src.services.flowpipe_service", "name": "ShowTimes"},
        },
    ],
    "subgraphs": [],
}