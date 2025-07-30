"""
  Copyright (c) 2016- 2025, Wiliot Ltd. All rights reserved.

  Redistribution and use of the Software in source and binary forms, with or without modification,
   are permitted provided that the following conditions are met:

     1. Redistributions of source code must retain the above copyright notice,
     this list of conditions and the following disclaimer.

     2. Redistributions in binary form, except as used in conjunction with
     Wiliot's Pixel in a product or a Software update for such product, must reproduce
     the above copyright notice, this list of conditions and the following disclaimer in
     the documentation and/or other materials provided with the distribution.

     3. Neither the name nor logo of Wiliot, nor the names of the Software's contributors,
     may be used to endorse or promote products or services derived from this Software,
     without specific prior written permission.

     4. This Software, with or without modification, must only be used in conjunction
     with Wiliot's Pixel or with Wiliot's cloud service.

     5. If any Software is provided in binary form under this license, you must not
     do any of the following:
     (a) modify, adapt, translate, or create a derivative work of the Software; or
     (b) reverse engineer, decompile, disassemble, decrypt, or otherwise attempt to
     discover the source code or non-literal aspects (such as the underlying structure,
     sequence, organization, ideas, or algorithms) of the Software.

     6. If you create a derivative work and/or improvement of any Software, you hereby
     irrevocably grant each of Wiliot and its corporate affiliates a worldwide, non-exclusive,
     royalty-free, fully paid-up, perpetual, irrevocable, assignable, sublicensable
     right and license to reproduce, use, make, have made, import, distribute, sell,
     offer for sale, create derivative works of, modify, translate, publicly perform
     and display, and otherwise commercially exploit such derivative works and improvements
     (as applicable) in conjunction with Wiliot's products and services.

     7. You represent and warrant that you are not a resident of (and will not use the
     Software in) a country that the U.S. government has embargoed for use of the Software,
     nor are you named on the U.S. Treasury Department’s list of Specially Designated
     Nationals or any other applicable trade sanctioning regulations of any jurisdiction.
     You must not transfer, export, re-export, import, re-import or divert the Software
     in violation of any export or re-export control laws and regulations (such as the
     United States' ITAR, EAR, and OFAC regulations), as well as any applicable import
     and use restrictions, all as then in effect

   THIS SOFTWARE IS PROVIDED BY WILIOT "AS IS" AND "AS AVAILABLE", AND ANY EXPRESS
   OR IMPLIED WARRANTIES OR CONDITIONS, INCLUDING, BUT NOT LIMITED TO, ANY IMPLIED
   WARRANTIES OR CONDITIONS OF MERCHANTABILITY, SATISFACTORY QUALITY, NONINFRINGEMENT,
   QUIET POSSESSION, FITNESS FOR A PARTICULAR PURPOSE, AND TITLE, ARE DISCLAIMED.
   IN NO EVENT SHALL WILIOT, ANY OF ITS CORPORATE AFFILIATES OR LICENSORS, AND/OR
   ANY CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY,
   OR CONSEQUENTIAL DAMAGES, FOR THE COST OF PROCURING SUBSTITUTE GOODS OR SERVICES,
   FOR ANY LOSS OF USE OR DATA OR BUSINESS INTERRUPTION, AND/OR FOR ANY ECONOMIC LOSS
   (SUCH AS LOST PROFITS, REVENUE, ANTICIPATED SAVINGS). THE FOREGOING SHALL APPLY:
   (A) HOWEVER CAUSED AND REGARDLESS OF THE THEORY OR BASIS LIABILITY, WHETHER IN
   CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE);
   (B) EVEN IF ANYONE IS ADVISED OF THE POSSIBILITY OF ANY DAMAGES, LOSSES, OR COSTS; AND
   (C) EVEN IF ANY REMEDY FAILS OF ITS ESSENTIAL PURPOSE.
"""
import time
import datetime
import pandas as pd
import os
import multiprocessing

from wiliot_core import set_logger, QueueHandler
from wiliot_tools.test_equipment.test_equipment import CognexNetwork, CognexDataMan
from wiliot_tools.association_tool.association_configs import is_wiliot_code
from wiliot_tools.association_tool.association_tool import CloudAssociation


class AssociatorProcess(CloudAssociation):
    def __init__(self, associate_q=None, stop_event=None, owner_id='', category_id='', time_btwn_request=1,
                 initiator_name=None, folder_path='', base_url=None):
        self.output_path = os.path.join(folder_path, f'association_output_{datetime.datetime.now().strftime("%Y%m%d_%H%M%S")}.csv')
        super().__init__(associate_q=associate_q, stop_event=stop_event, owner_id=owner_id,
                         is_gcp=False, category_id=category_id, time_btwn_request=time_btwn_request,
                         initiator_name=initiator_name,
                         logger_config={'dir_name': os.path.basename(os.path.dirname(folder_path)),
                                        'folder_name': os.path.basename(folder_path)},
                         base_url=base_url)

    def handle_results(self, message, asset_id, pixel_dict, bad_association):
        bad_association = super().handle_results(message, asset_id, pixel_dict, bad_association)
        element = {
                   'asset_code': [asset_id],
                   'wiliot_code': pixel_dict['pixel_id'],
                   'is_associated': [int(message['status_code'] // 100) == 2],
                   'associate_status_code': [message['status_code']],
                   'associate_msg': [message['data']],}
        df = pd.DataFrame(element)
        try:
            if os.path.isfile(self.output_path):
                df.to_csv(self.output_path, mode='a', header=False, index=False)
            else:
                df.to_csv(self.output_path, index=False)
        except Exception as e:
            self.logger.warning(f'AssociatorProcess: Could NOT save the following data due to {e}\n{df}')
        return bad_association


class ContinuousScanning:
    def __init__(self, host='', port=23, user_configs=None, stop_event=None):
        self.user_configs = user_configs
        run_name = self.user_configs.get('run_name', 'test').replace('.csv', '')
        logger_path, self.logger = set_logger('CognexNetworkCont', folder_name=f'{run_name}_{datetime.datetime.now().strftime("%Y%m%d_%H%M%S")}', file_name=run_name)
        self.stop_event = stop_event
        self.output_path = logger_path.replace('.log', '.csv')
        self.logger.info(f'the output csv file will be generate on: {self.output_path}')
        try:
            if host:
                self.scanner = CognexNetwork(timeout=0.1, host=host, telnet_port=int(port), log_name=self.logger.name)
            else:
                self.scanner = CognexDataMan(timeout=0.1, port=port, log_name=self.logger.name)
        except Exception as e:
            self.logger.warning(f'could not connect to network: {host}::{port} scanner due to: {e}')
            raise e
        
        
        self.do_association = self.user_configs.get('do_association', False)
        self.association_handler, self.associate_q = None, None
        if self.do_association:
            try:
                queue_handler = QueueHandler()
                self.associate_q = queue_handler.get_multiprocess_queue(queue_max_size=500)
                initiator_name = os.environ.get('StationName')
                kwargs = {'associate_q': self.associate_q,
                          'stop_event': stop_event,
                          'owner_id': self.user_configs.get('owner_id',''),
                          'category_id': self.user_configs.get('category_id',''),
                          'initiator_name': initiator_name,
                          'folder_path': os.path.dirname(logger_path),
                          'base_url': self.user_configs.get('base_url')
                          }
                # check cloud connection:
                self.association_handler = multiprocessing.Process(target=AssociatorProcess,
                                                                    kwargs=kwargs)

            except Exception as e:
                self.logger.warning(f'exception during TagAssociation init: {e}')
                raise e
            

    def run(self):
        if self.association_handler is not None:
                self.association_handler.start()
        while not self.is_stopped():
            try:
                self.scanner.trigger_on()
                codes_list = self.scanner.read_batch(wait_time=self.user_configs.get('time_per_loc', 1))
                if len(codes_list) == 0:
                    continue
                # scanned codes:
                code_list_str = ",".join(codes_list)
                self.logger.info(f'SCANNED,{code_list_str}')
                code_types = {'wiliot_code': [], 'asset_code': [], 'is_valid': False, 'timestamp': datetime.datetime.now().timestamp()}
                for c in codes_list:
                    if is_wiliot_code(c):
                        code_types['wiliot_code'].append(c)
                    elif self.user_configs.get('asset_str', '!!!') in c:
                        code_types['asset_code'].append(c)
                code_types = self.arrange_codes(code_types=code_types)
                new_df = pd.DataFrame({'wiliot_code': [code_types['wiliot_code'][0]], 'asset_code': [code_types['asset_code'][0]], 'timestamp': [datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S")], 'all_codes': [code_list_str]})
                self.save_file(new_df)
                self.add_to_association(code_types=code_types)
            except Exception as e:
                self.logger.warning(f'got exception during ContinuousScanning run: {e}')
                st = self.scanner.reconnect()
                if not st:
                    time.sleep(1)

        self.stop()
    
    def arrange_codes(self, code_types):
        if len(code_types['wiliot_code']) > 1:
            self.logger.warning(f'More then 1 Pixels were detected: {code_types["wiliot_code"]}')
            code_types['wiliot_code'] = ['']
        if len(code_types['asset_code']) > 1:
            self.logger.warning(f'More then 1 Assets were detected: {code_types["asset_code"]}')
            code_types['asset_code'] = ['']
        if len(code_types['wiliot_code']) == 0:
            self.logger.warning(f'No Pixel was detected')
            code_types['wiliot_code'] = ['']
        if len(code_types['asset_code']) == 0:
            self.logger.warning(f'No Assets was detected')
            code_types['asset_code'] = ['']
        code_types['is_valid'] = len(code_types['wiliot_code']) == 1 and len(code_types['asset_code']) == 1
        return code_types

    def save_file(self, df):
        try:
            if os.path.isfile(self.output_path):
                df.to_csv(self.output_path, mode='a', header=False, index=False)
            else:
                df.to_csv(self.output_path, index=False)
        except Exception as e:
            self.logger.warning(f'Could NOT save the following data due to {e}\n{df}')
        return
    
    def add_to_association(self, code_types):
        if code_types['is_valid'] and self.do_association:
            if self.associate_q.full():
                self.logger.warning(f'Could not add to assocaition queue since queue is full discard: {code_types}')
                return
            self.associate_q.put(code_types, block=False)
    
    def is_stopped(self):
        if self.stop_event is not None:
            return self.stop_event.is_set()
        return False
    
    def stop(self):
        self.scanner.trigger_off()
        time.sleep(0.1)
        self.scanner.close_port()
        if self.association_handler is not None:
                self.association_handler.join(10)
                if self.association_handler.is_alive():
                    self.logger.warning('associator process is still running')
        self.logger.info(f'ContinuousScanning run was completed, please check: {self.output_path}')


if  __name__ == '__main__':
    import argparse
    import keyboard
    import threading

    stop_event = multiprocessing.Event()
    def exit_func():
        while True:  # making a loop
            time.sleep(0.5)
            try:
                if keyboard.is_pressed('q'):
                    print('Exit app!')
                    stop_event.set()
                    break  # finishing the loop

            except Exception as e:
                print(e)
                break

    parser = argparse.ArgumentParser(description='Run Contiuous Scanner')
    parser.add_argument('-hn', '--host', default=None, help='host ip address')
    parser.add_argument('-pn', '--port', default=None, help='port number')
    parser.add_argument('-r', '--run_name', default=None, help='the run name for logging the output csv file')
    parser.add_argument('-t', '--time_per_loc', default=None, help='time per each location/box/frame')
    parser.add_argument('-a', '--asset_str', default=None, help='unique string inside the asset code')
    parser.add_argument('-d', '--do_association', default=0, help='True if assocaition is needed')
    parser.add_argument('-o', '--owner_id', default=None, help='The owner id number')
    parser.add_argument('-c', '--category_id', default=None, help='The owner id number')
    parser.add_argument('-b', '--base_url', default=None, help='The base url for instance https://api.us-east-2.prod.wiliot.cloud')

    args = parser.parse_args()
    user_configs={'run_name': args.run_name, 
                  'time_per_loc': float(args.time_per_loc), 
                  'asset_str': args.asset_str,
                  'do_association': args.do_association,
                  'owner_id': args.owner_id,
                  'category_id': args.category_id,
                  'base_url': args.base_url,
                  }
    cs =ContinuousScanning(host=args.host, port=args.port, 
                           stop_event=stop_event, user_configs=user_configs)
    exit_thread = threading.Thread(target=exit_func, args=())
    exit_thread.start()
    cs.run()
    print('done')