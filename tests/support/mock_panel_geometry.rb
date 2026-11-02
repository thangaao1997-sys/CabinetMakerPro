# encoding: UTF-8
# Minimal read-only stand-in for SketchUp's face/loop/edge geometry API.
# For CI mocks only. This is NOT an implementation of SketchUp's engine.
module Sketchup
  class Face; end unless const_defined?(:Face)
  class Edge; end unless const_defined?(:Edge)
end
class Numeric
  def to_mm; self; end
end
module MockPanelGeometry
  class Point
    attr_accessor :x, :y, :z
    def initialize(x,y,z); @x=x; @y=y; @z=z; end
  end
  class Vertex
    attr_reader :position
    def initialize(coords); @position=Point.new(*coords); end
  end
  class Loop
    attr_reader :vertices
    def initialize(coords); @vertices=coords.map{|xyz| Vertex.new(xyz)}; end
  end
  class Face < Sketchup::Face
    attr_reader :loops
    def initialize(*rings); @loops=rings.map{|coords| Loop.new(coords)};end
  end
  class Edge < Sketchup::Edge
    attr_reader :start, :end
    def initialize(a,b);@start=Vertex.new(a);@end=Vertex.new(b);end
  end
  def self.box(width, height, depth)
    a=[0,0,0];b=[width,0,0];c=[width,height,0];d=[0,height,0]
    e=[0,0,depth];f=[width,0,depth];g=[width,height,depth];h=[0,height,depth]
    rings=[
      [a,b,c,d],[e,f,g,h],[a,b,f,e],[b,c,g,f],[c,d,h,g],[d,a,e,h]
    ]
    edges=[
      [a,b],[b,c],[c,d],[d,a],[e,f],[f,g],[g,h],[h,e],
      [a,e],[b,f],[c,g],[d,h]
    ]
    rings.map{|ring|Face.new(ring)}+edges.map{|points|Edge.new(*points)}
  end
end
