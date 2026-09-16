BLENDER := /Applications/Blender.app/Contents/MacOS/Blender
BLEND   := build/f110.blend
SAMPLES ?= 128

.PHONY: all build verify render turntable export web stl viewer clean

all: build verify render export

build:                       ## generate geometry and assemble the .blend
	$(BLENDER) --background --python engine/assemble.py
	python3 tools/make_manifest.py

verify:
	python3 engine/verify.py
	python3 tools/audit_structure.py
	python3 tools/audit_geometry.py
	python3 tools/audit_watertight.py
	python3 tools/audit_intersect.py
	python3 tools/audit_manifest.py
	python3 tools/check_vendor.py
	node tools/validate_viewer.mjs .

render: 
	$(BLENDER) -b $(BLEND) -P engine/render.py -- all $(SAMPLES)

turntable: 
	$(BLENDER) -b $(BLEND) -P engine/render.py -- turntable 64

export: 
	$(BLENDER) -b $(BLEND) -P engine/export.py -- glb

web: 
	$(BLENDER) -b $(BLEND) -P engine/export.py -- web

stl: 
	$(BLENDER) -b $(BLEND) -P engine/export.py -- stl

viewer: 
	@echo "Serving http://localhost:8777/viewer/ — Ctrl-C to stop"
	@python3 -m http.server 8777 --bind 127.0.0.1

manifest: 
	python3 tools/make_manifest.py

clean:
	rm -rf build renders
