# encoding: UTF-8
require_relative '../plugin/ai_idea_v10/geometry_fingerprint'

module Sketchup
  class Face; end
  class Edge; end
end
class Numeric
  def to_mm; self; end
end
class SigPoint
  attr_accessor :x, :y, :z
  def initialize(x,y,z); @x=x;@y=y;@z=z;end
end
class SigVertex
  attr_reader :position
  def initialize(arr); @position=SigPoint.new(*arr);end
end
class SigLoop
  attr_reader :vertices
  def initialize(coords)
    @vertices=coords.map{|xyz|SigVertex.new(xyz)}
  end
end
class SigFace < Sketchup::Face
  attr_reader :loops
  def initialize(*rings)
    @loops=rings.map{|pts|SigLoop.new(pts)}
  end
end
class SigEdge < Sketchup::Edge
  attr_reader :start,:end
  def initialize(a,b)
    @start=SigVertex.new(a)
    @end=SigVertex.new(b)
  end
end
class SigEntities
  attr_reader :items
  def initialize(items);@items=items;end
  def to_a;@items;end
end

def expect(label)
  raise "FAILED: #{label}" unless yield
end

def cube_items
  p0=[0,0,0];p1=[10,0,0];p2=[10,20,0];p3=[0,20,0]
  p4=[0,0,30];p5=[10,0,30];p6=[10,20,30];p7=[0,20,30]
  rings=[
    [p0,p1,p2,p3],[p4,p5,p6,p7],
    [p0,p1,p5,p4],[p1,p2,p6,p5],
    [p2,p3,p7,p6],[p3,p0,p4,p7]
  ]
  edges=[
    [p0,p1],[p1,p2],[p2,p3],[p3,p0],
    [p4,p5],[p5,p6],[p6,p7],[p7,p4],
    [p0,p4],[p1,p5],[p2,p6],[p3,p7]
  ]
  rings.map{|ring|SigFace.new(ring)}+edges.map{|pair|SigEdge.new(*pair)}
end

baseline=cube_items
sig=AIIDEA::GeometryFingerprint.signature(SigEntities.new(baseline))
expect('1 valid digest') { sig.match?(/\A[0-9a-f]{64}\z/) }

shuffle_items=cube_items.reverse
expect('2 entity order invariant') {
  AIIDEA::GeometryFingerprint.signature(SigEntities.new(shuffle_items)) == sig
}

reverse_faces=cube_items
reverse_faces.each{|ent|ent.loops.each{|loop|loop.vertices.reverse!} if ent.is_a?(Sketchup::Face)}
expect('3 ring direction invariant') {
  AIIDEA::GeometryFingerprint.signature(SigEntities.new(reverse_faces)) == sig
}

extra_edge=cube_items
extra_edge << SigEdge.new([2,2,30],[7,2,30])
expect('4 internal edge changed without outside bounds') {
  AIIDEA::GeometryFingerprint.signature(SigEntities.new(extra_edge)) != sig
}

extra_face=cube_items
extra_face << SigFace.new([[1,1,30],[2,1,30],[1,2,30]])
expect('5 interior face changed') {
  AIIDEA::GeometryFingerprint.signature(SigEntities.new(extra_face)) != sig
}

hole=cube_items
hole[1].loops << SigLoop.new([[2,2,30],[5,2,30],[5,5,30],[2,5,30]])
expect('6 hole loop changed') {
  AIIDEA::GeometryFingerprint.signature(SigEntities.new(hole)) != sig
}

expect('7 reject unrecognized entities') do
  begin
    AIIDEA::GeometryFingerprint.signature(SigEntities.new(cube_items+[Object.new]))
    false
  rescue ArgumentError
    true
  end
end

expect('8 reject missing faces') do
  begin
    AIIDEA::GeometryFingerprint.signature(SigEntities.new([SigEdge.new([0,0,0],[1,1,1])]))
    false
  rescue ArgumentError
    true
  end
end

bad=cube_items
bad[0].loops[0].vertices[0].position.x=Float::INFINITY
expect('9 reject nonfinite coordinates') do
  begin
    AIIDEA::GeometryFingerprint.signature(SigEntities.new(bad))
    false
  rescue ArgumentError
    true
  end
end
puts 'AI IDEA geometry fingerprint mock: 9/9'
