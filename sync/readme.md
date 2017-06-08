# Real state indicators

## to run on the virtual machine´, first install rtree:
```bash
easy_install Rtree
```

then:
```python
python3 indicators_master.py
```


## to include large files:

### install git-lfs

```bash
curl -s https://packagecloud.io/install/repositories/github/git-lfs/script.deb.sh | os=debian dist=jessie sudo -E sudo bash

sudo apt-get install git-lfs

```
### before push
#### Add all zip files through Git LFS
```bash
git lfs track "*.zip"
```
#### Now you're ready to push some commits:
```
git add .gitattributes
git add my.zip
git commit -m "add zip"
```
#### You can confirm that Git LFS is managing your zip file:
```bash
git lfs ls-files
```
#### push
```bash
git push origin [your branch]
```



