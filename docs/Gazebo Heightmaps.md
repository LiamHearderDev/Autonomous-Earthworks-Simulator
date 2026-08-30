# How to implement an environment in Gazebo using heightmaps

**Prerequisites**

- Have Gazebo Harmonic installed
- Have a working Gazebo project directory
- Suggested: Have GIMP installed - makes it easy to make the required image files without trying to get good ones from the internet (for now as of Sprint 2 at least)  
Download Link: https://www.gimp.org/downloads/

-> **Open your chosen SDF file for editing**

The environment will be within it's own &lt;model&gt; tags as a model, so all other tags in the file can be left alone.

This is a template heightmap model:

```
<model name="terrain">
    <static>true</static>
    <link name="linkTerrain">
    <collision name="collision">
        <geometry>
        <heightmap>
            <uri>static/resources/[heightmapImage].png</uri>
            <size>int int int</size>
            <pos>int int int</pos>
        </heightmap>
        </geometry>
    </collision>
    <visual name="visual">
        <geometry>
        <heightmap>
            <uri>static/resources/[heightmapImage].png</uri>
            <size>int int int</size>
            <pos>int int int</pos>
            <texture>
                <size>int</size>
                <diffuse>static/resources/[diffuseTextureName].png</diffuse>
                <normal>static/resources/[normalMapName].png</normal>
            </texture>
            <blend>
                <min_height>int</min_height>
                <fade_dist>int</fade_dist>
            </blend>
        </heightmap>
        </geometry>
    </visual>
    </link>
</model>
```
Integers to be placed are 'int', all required images are assumed to be in static/resources.

Parts to be customised:

**The first &lt;heightmap&gt; under &lt;collision&gt;&lt;geometry&gt;**  

The &lt;uri&gt; tags will contain the path to the heightmap image that has these conditions:  
- Must be square (height=width), where the lengths are a power of two + 1 i.e of 2<sup>n</sup> + 1
- Must be grayscale with no transparency (no alpha channel)

To make one in GIMP:
- Make a new image with valid dimensions
- Make some noise in Filters > Render > Noise (try any option)
- Right-click on the background layer (or where the noise is) and click 'Remove Alpha Channel' if possible

The &lt;size&gt; tags should ideally have the X and Y dimensions of the heightmap image, though the Z dimension can be arbitrary

The &lt;pos&gt; value is an arbitrary 3D coordinate

**The second &lt;heightmap&gt;, under &lt;visual&gt;&lt;geometry&gt;**  

&lt;uri&gt;, &lt;size&gt; and &lt;pos&gt; will be the same as above. 

Under the &lt;texture&gt; tags:  

The &lt;size&gt; tags contain an int that represents the size of the square images that will be applied to the environment.

The &lt;diffuse&gt; tags will contain the path to the diffuse texture image, which defines the actual colour and look of the environment.  
To make a diffuse texture image in GIMP, it simply needs to have the same dimension conditions as above, and can then be any image/drawing you choose for the environment's appearance.

The &lt;normal&gt; tags contain the path to the normal map texture for the environment. This fakes the lighting of bumps, dents etc. without extra polygons.

To make a normal map in GIMP:
- Create a new image with the same dimension conditions
- Go to Filters > Generic > Normal Map to create one  
Note: Doing this on a blank image will create a default smooth normal map, you can draw over it after the filter to create custom ones!

The &lt;min_height&gt; and &lt;fade_dist&gt; under &lt;blend&gt; are self-explanatory, just int values.

**Useful resource for both parts**: https://sdformat.org/spec/1.4/geometry/#geometry_heightmap

And the overall spec for SDF: https://sdformat.org/spec/1.4/