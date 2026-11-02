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

      digest_data = {
        'schema' => 'ai-idea.panel-geometry.v1',
        'quantization_mm' => QUANT_MM,
        'faces' => face_data,
        'edges' => edge_data,
      }
      Digest::SHA256.hexdigest(JSON.generate(digest_data))
    rescue NoMethodError, TypeError, FloatDomainError => e
      raise ArgumentError, "Cannot inspect panel geometry: #{e.class}" 
    end
  end
end
