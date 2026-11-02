# encoding: UTF-8
# Read-only canonical geometry fingerprint for simple AI IDEA draft panels.
# Uses SketchUp face loops and edge endpoints, within the group's local axes.
# The SHA-256 value is change detection only; it is NOT a security signature.
require 'json'
require 'digest'

module AIIDEA
  module GeometryFingerprint
    module_function

    QUANT_MM = 0.01
    MAX_ENTITIES = 10_000

    def point_key(point)
      result = [point.x, point.y, point.z].map do |length|
        value = length.to_mm.to_f
        raise ArgumentError, 'Invalid geometry coordinate' unless value.finite?
        (value / QUANT_MM).round
      end
      raise ArgumentError, 'Invalid coordinate vector' unless result.length == 3
      result
    end

    def digest_components(face_data, edge_data)
      digest_data = {
        'schema' => 'ai-idea.panel-geometry.v1',
        'quantization_mm' => QUANT_MM,
        'faces' => face_data,
        'edges' => edge_data
      }
      Digest::SHA256.hexdigest(JSON.generate(digest_data))
    end

    # Derive the fingerprint of a true six-faced, twelve-edged rectangular
    # prism from the JSON dimensions alone, independently of SketchUp output.
    def expected_box_signature(x_mm, y_mm, z_mm)
      dims = [x_mm, y_mm, z_mm]
      unless dims.all? { |n| n.is_a?(Numeric) && n.finite? && n > 0 }
        raise ArgumentError, 'Invalid expected panel dimensions'
      end
      x,y,z = dims.map { |n| (n / QUANT_MM).round }
      raise ArgumentError, 'Panel too thin for geometry quantization' if [x,y,z].any?(&:zero?)
      p = [
        [0,0,0], [x,0,0], [x,y,0], [0,y,0],
        [0,0,z], [x,0,z], [x,y,z], [0,y,z]
      ]
      rings = [
        [0,1,2,3], [4,5,6,7], [0,1,5,4],
        [1,2,6,5], [2,3,7,6], [3,0,4,7]
      ]
      segments = [
        [0,1], [1,2], [2,3], [3,0],
        [4,5], [5,6], [6,7], [7,4],
        [0,4], [1,5], [2,6], [3,7]
      ]
      faces = rings.map { |ring| [ring.map { |i| p[i] }.sort] }.sort
      edges = segments.map { |segment| segment.map { |i| p[i] }.sort }.sort
      digest_components(faces, edges)
    end

    def signature(entities)
      raise ArgumentError, 'Cannot inspect geometry' unless entities.respond_to?(:to_a)
      items = entities.to_a
      raise ArgumentError, 'Too many or no geometry entities' unless items.length.between?(1, MAX_ENTITIES)
      unless items.all? { |entity| entity.is_a?(Sketchup::Face) || entity.is_a?(Sketchup::Edge) }
        raise ArgumentError, 'Unexpected nested or unsupported geometry entity'
      end
      faces = items.select { |entity| entity.is_a?(Sketchup::Face) }
      edges = items.select { |entity| entity.is_a?(Sketchup::Edge) }
      raise ArgumentError, 'Panel must have faces and edges' if faces.empty? || edges.empty?

      face_data = faces.map do |face|
        loops = face.loops
        raise ArgumentError, 'Face has no loops' unless loops.is_a?(Array) && !loops.empty?
        loops.map do |loop|
          vertices = loop.vertices
          raise ArgumentError, 'Broken face loop' unless vertices.is_a?(Array) && vertices.length >= 3
          vertices.map { |vertex| point_key(vertex.position) }.sort
        end.sort
      end.sort

      edge_data = edges.map do |edge|
        [point_key(edge.start.position), point_key(edge.end.position)].sort
      end.sort

      digest_components(face_data, edge_data)
    rescue NoMethodError, TypeError, FloatDomainError => e
      raise ArgumentError, "Cannot inspect panel geometry: #{e.class}" 
    end
  end
end
