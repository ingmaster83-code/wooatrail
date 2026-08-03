require 'json'

module Jekyll
  class TrailPageGenerator < Generator
    safe true
    priority :normal

    def generate(site)
      trails = load_json(site, '_rawdata/trails.json')
      mountains = load_json(site, '_rawdata/mountains.json')
      return if trails.empty? && mountains.empty?

      Jekyll.logger.info "TrailGenerator:", "#{trails.size}개 길 페이지 생성 중..."

      trails.each do |trail|
        next if trail['slug'].to_s.strip.empty?
        site.pages << TrailPage.new(site, trail)
      end

      Jekyll.logger.info "TrailGenerator:", "#{mountains.size}개 산/오름 페이지 생성 중..."

      mountains.each do |m|
        next if m['slug'].to_s.strip.empty?
        site.pages << MountainPage.new(site, m)
      end

      all_regions = (trails.map { |t| t['doNm'] } + mountains.map { |m| m['doNm'] }).uniq
      all_regions.each do |do_nm|
        next if do_nm.to_s.strip.empty?
        do_trails = trails.select { |t| t['doNm'] == do_nm }
        do_mountains = mountains.select { |m| m['doNm'] == do_nm }
        site.pages << RegionPage.new(site, do_nm, do_trails, do_mountains)
      end

      site.pages << SearchIndexPage.new(site, trails, mountains)

      Jekyll.logger.info "TrailGenerator:", "완료 (길 #{trails.size}개 + 산/오름 #{mountains.size}개)"
    end

    private

    def load_json(site, path)
      file = File.join(site.source, path)
      return [] unless File.exist?(file)
      JSON.parse(File.read(file, encoding: 'utf-8'))
    rescue => e
      Jekyll.logger.warn "TrailGenerator:", "#{path} 로드 실패: #{e.message}"
      []
    end
  end

  class TrailPage < Page
    def initialize(site, trail)
      @site = site
      @base = site.source
      @dir  = "trail/#{trail['slug']}"
      @name = 'index.html'

      self.process(@name)
      self.read_yaml(File.join(@base, '_layouts'), 'trail.html')
      trail_data = trail.dup
      trail_data['trailName'] = trail_data.delete('name')
      self.data.merge!(trail_data)
      self.data['layout']      = 'trail'
      self.data['title']       = build_title(trail)
      self.data['description'] = build_desc(trail)
    end

    private

    def build_title(t)
      loc = [t['doNm'], t['sigunguNm']].compact.join(' ')
      "#{t['name']} #{loc} 거리 소요시간"
    end

    def build_desc(t)
      loc = [t['doNm'], t['sigunguNm']].compact.join(' ')
      d = "#{loc} #{t['name']}. 총거리 #{t['distanceKm']}km, 소요시간 #{t['duration']}."
      d += " #{t['intro']}" if t['intro'].to_s.length > 3
      d[0, 155]
    end
  end

  class MountainPage < Page
    def initialize(site, m)
      @site = site
      @base = site.source
      @dir  = "mountain/#{m['slug']}"
      @name = 'index.html'

      self.process(@name)
      self.read_yaml(File.join(@base, '_layouts'), 'mountain.html')
      m_data = m.dup
      m_data['mountainName'] = m_data.delete('name')
      self.data.merge!(m_data)
      self.data['layout']      = 'mountain'
      self.data['title']       = build_title(m)
      self.data['description'] = build_desc(m)
    end

    private

    def build_title(m)
      loc = [m['doNm'], m['sigunguNm']].compact.join(' ')
      "#{m['name']} #{loc} 위치 정보"
    end

    def build_desc(m)
      loc = [m['doNm'], m['sigunguNm']].compact.join(' ')
      "#{loc} #{m['name']} 위치, 이용시간, 주차 정보를 확인하세요."[0, 155]
    end
  end

  class RegionPage < Page
    def initialize(site, do_nm, trails, mountains = [])
      @site = site
      @base = site.source
      @dir  = "region/#{do_nm}"
      @name = 'index.html'

      self.process(@name)
      self.read_yaml(File.join(@base, '_layouts'), 'region.html')
      self.data['layout']    = 'region'
      self.data['doNm']      = do_nm
      self.data['trails']    = trails
      self.data['mountains'] = mountains
      if trails.size > 0
        self.data['title']       = "#{do_nm} 둘레길·트레킹길 정보"
        self.data['description'] = "#{do_nm} 둘레길·트레킹길 #{trails.size}개, 산·오름 #{mountains.size}개 목록. 거리, 소요시간, 시작·종료 지점을 확인하세요."
      else
        self.data['title']       = "#{do_nm} 산·오름 정보"
        self.data['description'] = "#{do_nm} 산·오름 #{mountains.size}개 목록. 위치, 이용시간, 주차 정보를 확인하세요."
      end
    end
  end

  class SearchIndexPage < Page
    def initialize(site, trails, mountains = [])
      @site = site
      @base = site.source
      @dir  = ''
      @name = 'search_index.json'

      self.process(@name)
      self.data = { 'layout' => nil, 'sitemap' => false }

      trail_index = trails.map do |t|
        {
          'kind'        => 'trail',
          'slug'        => t['slug'],
          'name'        => t['name'],
          'doNm'        => t['doNm'],
          'sigunguNm'   => t['sigunguNm'],
          'distanceKm'  => t['distanceKm'],
          'duration'    => t['duration'],
          'intro'       => (t['intro'] || '')[0, 80],
        }
      end

      mountain_index = mountains.map do |m|
        {
          'kind'      => 'mountain',
          'slug'      => m['slug'],
          'name'      => m['name'],
          'doNm'      => m['doNm'],
          'sigunguNm' => m['sigunguNm'],
          'image'     => m['image'],
        }
      end

      index = trail_index + mountain_index

      self.content = index.to_json
    end

    def output   = self.content
    def render(layouts, registers); end
  end
end
