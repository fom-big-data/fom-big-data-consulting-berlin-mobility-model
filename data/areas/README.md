# Areas

* http://overpass-turbo.eu/
* get ID of area _Berlin_ (3600062422)

```
[out:json][timeout:25];
(
  area[name="Berlin"]["wikipedia"="de:Berlin"];
);
out body;
>;
out skel qt;
```

* query areas within Berlin

```
[out:json][timeout:25];
(
  node[QUERY](area:3600062422);
  way[QUERY](area:3600062422);
  relation[QUERY](area:3600062422);
);
out body;
>;
out skel qt;
```

* cemetery ```"landuse"~"cemetery"```
* commercial ```"landuse"~"commercial"```
* forest ```"landuse"~"forest"```
* garden ```"leisure"~"garden"```
* industrial ```"landuse"~"industrial"```
* park ```"leisure"~"park"```
* recreation_ground ```"landuse"~"recreation_ground"```
* residential ```"landuse"~"residential"```
