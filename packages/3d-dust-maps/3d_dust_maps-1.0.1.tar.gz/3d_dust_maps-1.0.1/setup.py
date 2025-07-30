from setuptools import setup, find_packages

setup(
    name="3d_dust_maps",
    version="1.0.1",  # 重要：更新版本号
    description="A lightweight 3D dust map tool with dynamic data downloading (Gaia + LAMOST).",
    author="Wang Tao",
    author_email="1026579743@qq.com",  # 可选，但建议添加
    url="https://github.com/Grapeknight/3d-dust-maps",
    packages=find_packages(),
    include_package_data=False,  # 重要：避免打包大文件
    install_requires=[
        "numpy",
        "pandas",
        "astropy",
        "astropy-healpix"
    ],
    python_requires=">=3.8",
    classifiers=[
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent",
    ],
)
