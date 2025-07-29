import os
import re
import sys
import glob
import json
import datetime
import shutil
import importlib
import subprocess
import traceback
from logger import logger
from junit_xml import JunitXml
sys.path.insert(0, os.getcwd())


class TARPublisher:
    def __init__(self, prod_name: str, temp: str, artifact: bool):
        self._artifact = artifact
        timestamp = self.generate_unique_timestamp()
        self._database = os.path.join(temp, prod_name, timestamp)
        self._features = dict()

    @staticmethod
    def generate_unique_timestamp():
        now = datetime.datetime.now()
        timestamp = now.strftime('%Y%m%d%H%M')
        return timestamp

    @staticmethod
    def find_videos(case_name: str) -> list:
        """
        find vide according to test case name
        """
        video_root = os.path.join('output', 'videos')
        video_dirs = [os.path.join(video_root, name) for name in os.listdir(video_root) if
                      os.path.isdir(os.path.join(video_root, name))]
        total_videos = []
        for video_dir in video_dirs:
            video_files = glob.glob(os.path.join(video_dir, f'{case_name}*.mp4'))
            for video_file in video_files:
                if re.match('[-0-9]+\.mp4', os.path.basename(video_file).replace(case_name, '')) is None:
                    continue
                else:
                    total_videos.append(video_file)
        return total_videos

    def prune_temp_data(self):
        # keep directories created within 5 days
        temp_data = os.path.dirname(self._database)
        # get dirs and files which created more than 5 days ago
        expired_data = [os.path.join(temp_data, name) for name in os.listdir(temp_data) if
                        datetime.datetime.fromtimestamp(os.path.getctime(
                            os.path.join(temp_data, name))) < datetime.datetime.now() - datetime.timedelta(days=5)]
        for data in expired_data:
            if os.path.isdir(data):
                shutil.rmtree(data)
            else:
                os.remove(data)
            logger.info(f'Remove {data} successfully.')

    def find_comparisons(self, module_name: str) -> tuple:
        """
        find image or json comparisons according to module name
        """
        mods = module_name.split('.')
        mod_path = '.'.join(mods[:-1])
        base_name = mods[-1]
        module = importlib.import_module(mod_path)
        logger.info(f'getting {base_name} from {module}.')
        resource_path = getattr(getattr(module, base_name), 'RESOURCE_PATH', None)
        if resource_path is None:
            return ()
        self._features.update({module_name: os.path.basename(resource_path)})
        assert os.path.isdir(resource_path), f'{resource_path} does not exist as a directory.'
        baseline_dir = os.path.join(resource_path, 'expected')
        baselines = []
        if os.path.isdir(baseline_dir):
            baselines = [os.path.join(baseline_dir, name) for name in os.listdir(baseline_dir) if
                         os.path.isfile(os.path.join(baseline_dir, name))]
        img_baselines = [file for file in baselines if file.endswith(('.png', '.jpg'))]
        json_baselines = [file for file in baselines if file.endswith('.json')]
        if len(img_baselines) + len(json_baselines) != len(baselines):
            logger.warning(f'Unexpected files in {baselines}')
        img_actuals = list()
        del_indexes = list()
        for ind, img_base in enumerate(img_baselines):
            img_actual = img_base.replace('expected', 'actual')
            if os.path.isfile(img_actual):
                img_actuals.append(img_actual)
            else:
                del_indexes.append(ind)
        del_indexes.sort(reverse=True)
        for ind in del_indexes:
            del img_baselines[ind]
        json_actuals = list()
        del_indexes = list()
        for ind, json_base in enumerate(json_baselines):
            json_actual = json_base.replace('expected', 'actual')
            if os.path.isfile(json_actual):
                json_actuals.append(json_actual)
            else:
                del_indexes.append(ind)
        del_indexes.sort(reverse=True)
        for ind in del_indexes:
            del json_baselines[ind]
        assert len(img_baselines) == len(img_actuals), f'Count of {img_baselines} and {img_actuals} are not equal.'
        assert len(json_baselines) == len(json_actuals), f'Count of {json_baselines} and {json_actuals} are not equal.'
        return (img_baselines, img_actuals), (json_baselines, json_actuals)

    def publish_result(self) -> str:
        res_xmls = glob.glob(os.path.join('output', 'results', 'py_result-*.xml'))
        assert len(res_xmls) == 1, f'There should be only one xml file: {res_xmls}'
        os.makedirs(self._database)
        res_xml = res_xmls[0]
        result_dir = os.path.join(self._database, 'result')
        os.mkdir(result_dir)
        shutil.copyfile(res_xml, os.path.join(result_dir, os.path.basename(res_xml)))
        shutil.make_archive(result_dir, 'zip', result_dir)
        return res_xml

    def publish_artifact(self, xml_file: str):
        artifact_dir = os.path.join(self._database, 'artifact')
        images_root = os.path.join(artifact_dir, 'images')
        jsons_root = os.path.join(artifact_dir, 'jsons')
        videos_root = os.path.join(artifact_dir, 'videos')
        scripts_root = os.path.join(artifact_dir, 'scripts')
        os.makedirs(images_root)
        os.mkdir(jsons_root)
        os.mkdir(videos_root)
        os.mkdir(scripts_root)
        artifact_obj = dict()
        for case_name, class_name in JunitXml(xml_file).generate_test_cases():
            artifact_val = dict()
            logger.info(f'Collect artifact for test case: {case_name}')
            video_files = self.find_videos(case_name)
            if video_files:
                for video_file in video_files:
                    logger.info(f'video file: {video_file}')
                    converted_video = os.path.join(videos_root, os.path.basename(video_file))
                    if os.path.isfile(converted_video):
                        logger.warning(f'The video {converted_video} already exists.')
                    else:
                        cmd = f'ffmpeg -y -i "{video_file}" -vcodec h264 "{converted_video}" -nostats -loglevel 0'
                        try:
                            subprocess.check_call(cmd, shell=True)
                        except:
                            logger.warning(f'Failed to convert video: {video_file}')
                            logger.warning(traceback.format_exc())
                        else:
                            logger.info(f'Convert video successfully: {converted_video}')
                            act_video = os.path.relpath(converted_video, self._database)
                            if 'video' in artifact_val:
                                artifact_val['video'].append({'actual': act_video})
                            else:
                                artifact_val['video'] = [{'actual': act_video}]
            comparisons = self.find_comparisons(class_name)
            if comparisons:
                for ind, comparison in enumerate(comparisons):
                    is_img = ind == 0
                    _, actuals = comparison
                    if actuals:
                        feature = self._features[class_name]
                        if is_img:
                            logger.info(f'images: {comparison}')
                            artifact_type = 'image'
                            feature_dir = os.path.join(images_root, feature)
                        else:
                            logger.info(f'jsons: {comparison}')
                            artifact_type = 'json'
                            feature_dir = os.path.join(jsons_root, feature)
                        artifact_val[artifact_type] = list()
                        for base, act in zip(*comparison):
                            expected_dir = os.path.join(feature_dir, 'expected')
                            actual_dir = os.path.join(feature_dir, 'actual')
                            os.makedirs(expected_dir, exist_ok=True)
                            os.makedirs(actual_dir, exist_ok=True)
                            base = shutil.copyfile(base, os.path.join(expected_dir, os.path.basename(base)))
                            act = shutil.copyfile(act, os.path.join(actual_dir, os.path.basename(act)))
                            base_rel = os.path.relpath(base, self._database)
                            act_rel = os.path.relpath(act, self._database)
                            diff = os.path.join('test_data', feature, 'diff', os.path.basename(act))
                            if os.path.isfile(diff):
                                diff_dir = os.path.join(feature_dir, 'diff')
                                os.makedirs(diff_dir, exist_ok=True)
                                diff = shutil.copyfile(diff, os.path.join(diff_dir, os.path.basename(diff)))
                                diff_rel = os.path.relpath(diff, self._database)
                                artifact_val[artifact_type].append({'baseline': base_rel, 'actual': act_rel, 'diff': diff_rel})
                            else:
                                artifact_val[artifact_type].append({'baseline': base_rel, 'actual': act_rel})
            script_file = os.path.join(*class_name.split('.')[:-1]) + '.py'
            if not os.path.isfile(script_file):
                logger.warning(f'The script {script_file} does not exist.')
            else:
                act = shutil.copyfile(script_file, os.path.join(scripts_root, case_name + '.py'))
                act_script = os.path.relpath(act, self._database)
                artifact_val['script'] = [{'actual': act_script}]
            if artifact_val:
                artifact_obj[case_name] = artifact_val
        shutil.make_archive(artifact_dir, 'zip', artifact_dir)
        logger.info(artifact_obj)
        return artifact_obj

    def publish_jsons(self, artifact_obj: dict):
        # dump artifact object to a json file
        artifact_json = os.path.join(self._database, 'artifact.json')
        with open(artifact_json, 'w') as wf:
            json.dump(artifact_obj, wf, indent=4)

        default_info = 'UNKNOWN'
        info = {
            'Build Reason': 'Schedule' if os.getenv('BUILD_REASON') == 'Schedule' else f'Manual By {os.getenv("BUILD_REQUESTEDFOR", default_info)}',
            'Product Build Branch': 'release' if 'release' in os.getenv('BUILD_SOURCEBRANCHNAME', default_info).lower() else 'trunk',
            'Product Build Version': os.getenv('LATEST_VERSION', default_info),
            'Pipeline': os.getenv('BUILD_DEFINITIONNAME', default_info),
            'Pipeline Run': f'https://dev.azure.com/hexagonmi/DE-VirtualManufacturing/_build/results?buildId={os.environ["BUILD_BUILDID"]}' if os.getenv("BUILD_BUILDID") else default_info,
            'Pipeline Run Datetime': datetime.datetime.now().strftime("%B %d %H:%M:%S"),
            'Xray Execution Link': f'https://hexagon.atlassian.net/browse/{os.environ["XRAY_EXECUTION_ID"]}' if os.getenv("XRAY_EXECUTION_ID") else default_info,
        }

        # dump information to a json file
        info_json = os.path.join(self._database, 'info.json')
        with open(info_json, 'w') as wf:
            json.dump(info, wf, indent=4)

    def publish(self):
        self.publish_jsons(self.publish_artifact(self.publish_result()))
        if self._artifact:
            complete_flag = os.path.join(self._database, 'tar_complete')
            with open(complete_flag, 'w') as wf:
                pass
            logger.info(f'Create complete flag at {complete_flag}.')
            print(f'##vso[artifact.upload artifactname=tar_{os.path.basename(self._database)}]{self._database}')
        logger.info('All is published.')
        try:
            self.prune_temp_data()
        except:
            logger.warning('Failed to prune temp data.')
            logger.warning(traceback.format_exc())
            pass


def main():
    valid_prods = ('Simufact Forming', 'Simufact Welding', 'Simufact Additive', 'FTI FormingSuite')
    args = sys.argv[1:]
    args_len = len(args)
    prod_name = None
    temp = os.path.join(os.environ['userprofile'], 'temp_tar')
    artifact = False
    for i in range(args_len):
        if args[i] == '-p' and i+1 < args_len:
            prod_name = args[i+1]
        elif args[i] == '-t' and i+1 < args_len:
            temp = args[i+1]
        elif args[i] == '-a':
            artifact = True

    if prod_name is None or prod_name not in valid_prods:
        logger.error(f'usage: python publish-tar -p <prodName> [-t <temp>] [-a],'
                     f'the valid product names:{" ".join(valid_prods)}')
        sys.exit(-1)
    TARPublisher(prod_name, temp, artifact).publish()
