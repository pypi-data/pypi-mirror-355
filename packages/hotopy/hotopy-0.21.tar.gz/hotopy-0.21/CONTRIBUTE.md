## How to contribute

Generally checkout the [NumPy developer docs](https://numpy.org/doc/stable/dev/howto-docs.html) and setup your git first.

Clone the repository and setup pre-commit hooks
```commandline
git clone git@gitlab.gwdg.de:irp/hotopy.git
cd hotopy
```

(Optional) Create a venv and launch it to your current shell
```commandline
python3 -m venv venv --prompt HoToPy
source venv/bin/activate
```

Install `hotopy` module in editable mode (note: you may add the `--user` flag if you are not using venv's)
```commandline
pip install -e '.[dev,docs,tomo]'
pre-commit install
```

Make a new branch for the new feature / fix you want to develop.
```commandline
git checkout -b <usefulandshortname>
```

Write the code. Make sure by running pre-commit it does not raise errors or warnings. You can check this anytime
by running 
```commandline
pre-commit
```

Push your code to the corresponding branch in the remote repository.
```commandline
git push -u origin HEAD
```

At this point other people can see your code, but it is not part of the master branch, so you can get feedback and help without having to worry about breaking anything.

When you are happy and think, your adjustments should be included in the master
branch, create a merge request on the Gitlab website. Someone else will then check your code and merge it into the master branch if appropriate.

Only when you know what you are doing and are certain not to break anything, small changes can also be pushed directly to the master branch.
