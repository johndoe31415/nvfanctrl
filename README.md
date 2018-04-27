# nvfanctrl
nvfanctrl is a tool that regulates the fan PWM of your NVidia graphics card by
software. In particular, modern NVidia cards will have a stopped fan for the
most time but as soon as they hit about 55°C, they'll spin up to 60% PWM. This
means that for my particular system, for example, there was a spin-up of the
fan about every five minutes or so for about 30 seconds. Super annoying. With
nvfanctrl, you can just give it a setpoint, a minimum fan PWM percentage and
it'll happily regulate away.

## Usage
Using nvfanctrl is straightforward:

```
$ ./nvfanctrl.py --help
usage: nvfanctrl.py [-h] [-t temp] [-i secs] [--regulation-deadzone temp]
                    [--initial-pwm %] [--min-speed %] [--max-speed %]
                    [--fan fan_id] [--gpu gpu_id] [--daemonize] [-v]

optional arguments:
  -h, --help            show this help message and exit
  -t temp, --target-temp temp
                        Specifies the GPU target temperature in °C. Defaults
                        to 55°C
  -i secs, --regulation-interval secs
                        Gives the interval in which the fan target is checked
                        and adjustments are made. Defaults to 2.5 seconds.
  --regulation-deadzone temp
                        Gives the deadzone, i.e. +- degrees C in which not to
                        change regulation parameters. Defaults to +-3.0°C.
  --initial-pwm %       When initially starting, gives the initial PWM duty
                        cycle in percent that should be given to the fan.
                        Defaults to 50%.
  --min-speed %         Defines the minimum fan target speed in percent that
                        is chosen.
  --max-speed %         Defines the maximum fan target speed in percent that
                        is chosen.
  --fan fan_id          The ID of the fan that should be regulated. Defaults
                        to fan:0.
  --gpu gpu_id          The ID of the GPU that should be regulated. Defaults
                        to gpu:0.
  --daemonize           Fork into background (but do not make init the parent
                        process, so that nvfanctrl terminates when the X
                        session terminates as well).
  -v, --verbose         Be more verbose.
```

So, for example, if you want your temperature to be regulated to 55°C, do:

```
$ ./nvfanctrl.py -t 55 
```

That's it, pretty much. Well, actually you'll have to need to enable software
fan control in the first place, but that's covered in the next section.

## Installation
To permanently install nvfanctrl, you'll first have to enable setting the fan
temperature on your NVidia card. By default, this isn't possible. On a Ubuntu
system, therefore create (as root) a file in `/usr/share/X11/xorg.conf.d` that
you call `99-nvidia-coolbits.conf`. Use this content:

```
Section "Device"
	Identifier "Device0"
	Driver "nvidia"
	VendorName "NVIDIA Corporation"
	Option "Coolbits" "4"
EndSection
```

This will alllow fan regulation at the next restart of your X server. Then,
just create a startup entry of your favorite window manager (Mate, obviously):

```
/home/joe/amazing_software/nvfanctrl/nvfanctrl.py -t 55 --daemonize
```

And you should be set.

## License
GNU GPL-3.
