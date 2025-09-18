# GIU Staff Schedule Composer - Deployment Guide

## 🚀 Quick Start

### Development Setup

1. **Clone the repository**
```bash
git clone <repository-url>
cd claude-giu
```

2. **Backend Setup**
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

3. **Environment Configuration**
```bash
cp .env.example .env
# Edit .env with your settings
```

4. **Start Backend**
```bash
uvicorn main:app --reload
```

5. **Frontend Setup** (in new terminal)
```bash
cd frontend
npm install
npm start
```

6. **Access the Application**
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

## 🐳 Docker Deployment

### Prerequisites
- Docker
- Docker Compose

### Quick Deployment
```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

### Production Deployment
```bash
# Build and start with production config
docker-compose -f docker-compose.prod.yml up -d

# Scale backend if needed
docker-compose up -d --scale backend=3
```

## 🌐 Production Setup

### Environment Variables

#### Backend (.env)
```bash
DATABASE_URL=postgresql://user:password@db:5432/scheduler
SECRET_KEY=your-super-secret-production-key
CORS_ORIGINS=https://yourdomain.com
```

#### Frontend (.env)
```bash
REACT_APP_API_URL=https://api.yourdomain.com
```

### SSL Configuration

1. **Get SSL certificates** (Let's Encrypt recommended)
```bash
certbot certonly --webroot -w /var/www/certbot -d yourdomain.com
```

2. **Update nginx configuration** with SSL paths

3. **Restart services**
```bash
docker-compose restart nginx
```

## 📊 Database Setup

### SQLite (Development)
- Automatic setup, no configuration needed
- Database file: `backend/scheduler.db`

### PostgreSQL (Production)
1. **Initialize database**
```bash
docker-compose exec db psql -U scheduler_user -d scheduler
```

2. **Run migrations** (if using Alembic)
```bash
docker-compose exec backend alembic upgrade head
```

### Database Backup
```bash
# Backup
docker-compose exec db pg_dump -U scheduler_user scheduler > backup.sql

# Restore
docker-compose exec -T db psql -U scheduler_user scheduler < backup.sql
```

## 🔧 Configuration Options

### Scheduling Policies
Default configuration in backend settings:
- Tutorial-Lab Independence: OFF
- Equal Count Policy: OFF
- Number Matching Policy: OFF
- Fairness Mode: OFF

### Performance Tuning

#### Backend
- **Workers**: Adjust `--workers` in uvicorn command
- **Database Connections**: Configure SQLAlchemy pool settings
- **Caching**: Add Redis for caching (optional)

#### Frontend
- **Build Optimization**: Already configured in Dockerfile
- **CDN**: Consider using CDN for static assets

## 🔐 Security Considerations

### Authentication
- JWT tokens with configurable expiration
- Secure password hashing with bcrypt
- Role-based access control (Admin/Staff)

### API Security
- CORS configuration
- Input validation with Pydantic
- SQL injection protection with SQLAlchemy
- Rate limiting (add nginx rate limiting)

### Infrastructure Security
- Use strong passwords for database
- Keep Docker images updated
- Configure firewall rules
- Regular security updates

## 📈 Monitoring & Logging

### Health Checks
- Backend: `/health` endpoint
- Frontend: nginx health check
- Database: connection monitoring

### Logging
```bash
# View application logs
docker-compose logs backend
docker-compose logs frontend

# Follow logs in real-time
docker-compose logs -f
```

### Metrics (Optional)
Add Prometheus + Grafana for monitoring:
1. CPU, memory usage
2. API response times
3. Database performance
4. Schedule generation success rates

## 🔄 Updates & Maintenance

### Application Updates
```bash
# Pull latest changes
git pull origin main

# Rebuild and restart
docker-compose down
docker-compose build
docker-compose up -d
```

### Database Migrations
```bash
# Create migration
docker-compose exec backend alembic revision --autogenerate -m "description"

# Apply migration
docker-compose exec backend alembic upgrade head
```

### Backup Strategy
1. **Daily database backups**
2. **Weekly full system backup**
3. **Configuration files backup**
4. **SSL certificates backup**

## 🐛 Troubleshooting

### Common Issues

1. **Backend won't start**
   - Check database connection
   - Verify environment variables
   - Check port availability

2. **Frontend can't connect to backend**
   - Verify API URL in frontend env
   - Check CORS settings
   - Confirm backend is running

3. **Database connection errors**
   - Check database credentials
   - Ensure database container is running
   - Verify network connectivity

4. **Permission issues**
   - Check file permissions
   - Verify Docker user permissions
   - SELinux context (if applicable)

### Debug Commands
```bash
# Check container status
docker-compose ps

# Enter container for debugging
docker-compose exec backend bash
docker-compose exec frontend sh

# View container resources
docker stats

# Check networks
docker network ls
docker network inspect claude-giu_default
```

## 📞 Support

### Logs Location
- Backend logs: `docker-compose logs backend`
- Frontend logs: `docker-compose logs frontend`
- Database logs: `docker-compose logs db`
- Nginx logs: `docker-compose logs nginx`

### Performance Monitoring
- API response times via `/health` endpoint
- Database query performance
- Memory and CPU usage via `docker stats`

For additional support, check the application logs and ensure all services are running properly with `docker-compose ps`.