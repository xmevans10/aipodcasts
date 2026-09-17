--- Aurora: a radial spectrum ring with sparks, computed every frame.
--- The five band inputs come from the episode's own audio envelope, so the ring
--- is the shape of the narration rather than a loop.

local SPOKES = 120
local CENTER_Y = 214
local BASE_RADIUS = 118
local REACH = 74

type Spark = { angle: number, radius: number, speed: number, life: number, size: number }

type Aurora = {
	band1: Input<number>,
	band2: Input<number>,
	band3: Input<number>,
	band4: Input<number>,
	band5: Input<number>,
	level: Input<number>,

	path: Path,
	sparkPath: Path,
	ring: Paint,
	glow: Paint,
	spark: Paint,
	size: Vector,
	elapsed: number,
	spin: number,
	sparks: { Spark },
	emitted: number,
	wasQuiet: boolean,
}

local function bands(self: Aurora): { number }
	return { self.band1, self.band2, self.band3, self.band4, self.band5 }
end

--- Band energy for a spoke, mirrored left to right so the ring reads as one shape.
local function energyAt(self: Aurora, t: number): number
	local mirrored = 1 - math.abs(2 * t - 1)
	local values = bands(self)
	local position = mirrored * 4
	local low = math.floor(position)
	local high = math.min(4, low + 1)
	local blend = position - low
	return values[low + 1] * (1 - blend) + values[high + 1] * blend
end

local function buildRing(self: Aurora)
	self.path:reset()
	local center = Vector.xy(self.size.x * 0.5, CENTER_Y)
	for i = 0, SPOKES - 1 do
		local t = i / SPOKES
		local angle = t * math.pi * 2 + self.spin
		-- two slow waves keep the ring alive even between syllables
		local ripple = math.sin(angle * 3 + self.elapsed * 1.7) * 3
			+ math.sin(angle * 5 - self.elapsed * 1.1) * 2
		local radius = BASE_RADIUS + energyAt(self, t) * REACH + ripple
		local point = Vector.xy(center.x + math.cos(angle) * radius, center.y + math.sin(angle) * radius * 0.92)
		if i == 0 then
			self.path:moveTo(point)
		else
			self.path:lineTo(point)
		end
	end
	self.path:close()
end

local function emit(self: Aurora, count: number)
	for _ = 1, count do
		local angle = math.random() * math.pi * 2
		table.insert(self.sparks, {
			angle = angle,
			radius = BASE_RADIUS + math.random() * 24,
			speed = 34 + math.random() * 62,
			life = 1,
			size = 1.6 + math.random() * 2.6,
		})
	end
end

local function advanceSparks(self: Aurora, seconds: number)
	local index = 1
	while index <= #self.sparks do
		local spark = self.sparks[index]
		spark.radius += spark.speed * seconds
		spark.angle += seconds * 0.22
		spark.life -= seconds * 0.55
		if spark.life <= 0 then
			table.remove(self.sparks, index)
		else
			index += 1
		end
	end
end

function init(self: Aurora, context: Context): boolean
	return true
end

function resize(self: Aurora, size: Vector, scale: number)
	self.size = size
end

function advance(self: Aurora, seconds: number): boolean
	self.elapsed += seconds
	self.spin += seconds * (0.08 + self.level * 0.42)
	advanceSparks(self, seconds)

	-- a spark burst on each rise out of quiet: the consonants and sentence starts
	if self.level > 0.42 and self.wasQuiet then
		emit(self, 3 + math.floor(self.level * 7))
		self.wasQuiet = false
	elseif self.level < 0.26 then
		self.wasQuiet = true
	end
	return true
end

function draw(self: Aurora, renderer: Renderer)
	buildRing(self)
	self.glow.feather = 26 + self.level * 34
	self.glow.color = Color.rgba(255, 255, 255, math.floor(26 + self.level * 54))
	renderer:drawPath(self.path, self.glow)

	self.ring.thickness = 1.5 + self.level * 2.4
	self.ring.color = Color.rgba(255, 255, 255, math.floor(60 + self.level * 120))
	renderer:drawPath(self.path, self.ring)

	if #self.sparks > 0 then
		self.sparkPath:reset()
		local center = Vector.xy(self.size.x * 0.5, CENTER_Y)
		for _, spark in self.sparks do
			local x = center.x + math.cos(spark.angle) * spark.radius
			local y = center.y + math.sin(spark.angle) * spark.radius * 0.92
			local size = spark.size * spark.life
			self.sparkPath:moveTo(Vector.xy(x - size, y))
			self.sparkPath:quadTo(Vector.xy(x, y - size), Vector.xy(x + size, y))
			self.sparkPath:quadTo(Vector.xy(x, y + size), Vector.xy(x - size, y))
			self.sparkPath:close()
		end
		self.spark.color = Color.rgba(255, 255, 255, 170)
		renderer:drawPath(self.sparkPath, self.spark)
	end
end

return function(context: Context): Layout<Aurora>
	return {
		band1 = 0, band2 = 0, band3 = 0, band4 = 0, band5 = 0, level = 0,
		path = Path.new(),
		sparkPath = Path.new(),
		ring = Paint.with({ color = Color.rgba(255, 255, 255, 90), style = 'stroke', thickness = 2, join = 'round', cap = 'round' }),
		glow = Paint.with({ color = Color.rgba(255, 255, 255, 40), style = 'stroke', thickness = 10, join = 'round', feather = 26 }),
		spark = Paint.with({ color = Color.rgba(255, 255, 255, 180), style = 'fill', feather = 2 }),
		size = Vector.xy(500, 500),
		elapsed = 0,
		spin = 0,
		sparks = {},
		emitted = 0,
		wasQuiet = true,
		init = init, resize = resize, advance = advance, draw = draw,
	}
end
