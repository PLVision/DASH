# General changes
* Added [SAI-Challenger](https://github.com/PLVision/SAI-Challenger.OCP) submodule by path: DASH/test/SAI-Challenger.OCP.
* Added [cgyang](https://github.com/mgheorghe/cgyang) submodule by path: DASH/test/third-party/cgyang.
* Added test cases for SAI-Challenger by path: DASH/test/test-cases/test_vector_example

# New make targets:
**build-saic-client**: Build SAI-Challenger docker image and docker image based on SAI-Challenger client docker image with sai_thrift, saigen and DASH files.

**run-saic-client**: Start Ixia-C and docker container sc-client-thrift-run from image built on build-saic-client target. SAI-Challenger tests (DASH/test/SAI-Challenger.OCP/tests) folder replaced by DASH/test/test-cases/test_vector_example folder inside of container. Binded mount volume with DASH folder.

**kill-saic-client**: Stop Ixia-C and sc-client-thrift-run container.

**run-saic-test-thrift**: Run test manually. This target may be triggerred with passing parameters, or with default parameters.  
Run with default parameters(Setup file: ../setups/sai_dpu_client_server.json; Test: all tests):
```
make run-saic-test-thrift
```
Run with setup parameter and default test parameter (All tests):
```
make run-saic-test-thrift <setup_file>
```
Run with setup parameter and test parameter:
```
make run-saic-test-thrift <setup_file> <test_name>
```

# How to start
## Prepare repository
```
git clone https://github.com/PLVision/DASH.git
cd DASH && git checkout dev-tests-extension
git submodule update --init --recursive
```

## Build environment
```
cd dash-pipeline
make clean && make all
```

## Start environment
Run in the 3 separate windows/tabs.
```
make run-switch
make run-saithrift-server
make run-saic-client
```

## Run tests manually
Execute test inside the docker `sc-client-thrift-run` container or by `docker exec sc-client-thrift-run <command>` or by `run-saic-test-thrift` target.

### Pure SAI tests run
```
Via Make target:
make run-saic-test-thrift sai_dpu_client_server_snappi.json test_vnet_inbound.py
make run-saic-test-thrift sai_dpu_client_server_snappi.json test_vnet_outbound.py

Via docker exec:
pytest -sv --setup=sai_dpu_client_server_snappi.json test_vnet_inbound.py
pytest -sv --setup=sai_dpu_client_server_snappi.json test_vnet_outbound.py
```

### Test Vector format tests
```
Via Make target:
make run-saic-test-thrift sai_dpu_client_server_snappi.json test_sai_vnet_inbound.py
make run-saic-test-thrift sai_dpu_client_server_snappi.json test_sai_vnet_outbound.py

Via docker exec:
pytest -sv --setup=sai_dpu_client_server_snappi.json test_sai_vnet_inbound.py
pytest -sv --setup=sai_dpu_client_server_snappi.json test_sai_vnet_outbound.py
```

# Known issues
* [Test Vector format tests ](#Test Vector format tests): traffic check will fail as expected
