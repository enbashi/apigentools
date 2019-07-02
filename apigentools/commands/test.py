import logging
import os
import subprocess

from apigentools.commands.command import Command
from apigentools.utils import run_command

log = logging.getLogger(__name__)


class TestCommand(Command):
    def get_test_df_name(self, lang, version):
        return os.path.join(
            self.get_generated_lang_dir(lang),
            "Dockerfile.test.{}".format(version)
        )

    def build_test_image(self, df_path, img_name):
        if os.path.exists(df_path):
            build = [
                "docker",
                "build",
                os.path.dirname(df_path),
                "-f",
                df_path,
                "-t",
                img_name,
            ]
            if self.args.no_cache:
                build.append("--no-cache")
            run_command(build)
            return img_name
        return None

    def run_test_image(self, img_name):
        log.info("Running tests: %s", img_name)
        run_command([
            "docker",
            "run",
            img_name
        ])

    def run(self):
        cmd_result = 0
        for lang_name, lang_config in self.config.language_configs.items():
            for version in lang_config.spec_versions:
                df_path = self.get_test_df_name(lang_name, version)
                img_name = "apigentools-test-{lang}-{version}".format(
                    lang=lang_name, version=version
                )
                log.info(
                    "Looking up %s to test language %s, version %s",
                    df_path, lang_name, version
                )

                # first, try building the image
                if not os.path.exists(df_path):
                    log.info("PASS: Could not find %s, skipping", df_path)
                    continue
                try:
                    img_name = self.build_test_image(df_path, img_name)
                    log.info("SUCCESS: built %s", img_name)
                except subprocess.CalledProcessError:
                    log.error(
                        "FAIL: Failed to build testing image for language %s, spec version %s",
                        lang_name, version
                    )
                    cmd_result = 1
                    continue

                # if building was successful, run the image
                try:
                    self.run_test_image(img_name)
                    log.info("SUCCESS: ran %s", img_name)
                except subprocess.CalledProcessError:
                    log.error(
                        "ERROR: Testing failed for language %s, spec version %s",
                        lang_name, version
                    )
                    cmd_result =  1
        return cmd_result